"""Script to subscribe to fastly pub/sub messages and write to logging."""

import json
import logging
import os
import signal
from collections import deque
from datetime import datetime
from threading import Condition, Thread
from time import perf_counter
from typing import List, Tuple

import google.auth
from google.api_core.exceptions import PermissionDenied
from google.cloud import pubsub_v1, logging as gcp_logging
from google.cloud.logging_v2.entries import Resource
from google.cloud.pubsub_v1.subscriber.message import Message

from arxiv.ops.fastly_log_ingest import Rate

PROJECT_ID = os.environ.get("PROJECT_ID", "arxiv-production")
SUBSCRIPTION_ID = os.environ.get("SUBSCRIPTION_ID", "logs-fastly-arxiv-org-sub")

LOGGER_NAME = os.environ.get("LOGGER_NAME", "fastly_log_ingest")
"""Name of logger in GCP, don't prefix with project-id or anything."""

THREADS = int(os.environ.get("THREADS", 1))
"""Number of threads to use to send logs"""

SEND_PERIOD = int(os.environ.get("SEND_PERIOD", 8.0))
"""seconds to wait for messages to accumulate"""

PREFERRED_PER_BATCH = int(os.environ.get("PREFERRED_PER_BATCH", 50))
"""Number of records in a batch to start sending to log. Must be smaller than MAX_PER_BATCH"""

MAX_PER_BATCH = int(os.environ.get("MAX_PER_BATCH", 100))
"""Number of log records in a batch. Limit seems to be 16kb but not sure."""

MAX_BYTES_PER_VALUE = int(os.environ.get("MAX_BYTES_PER_VALUE", 1024 * 2))
"""Maximum number of bytes allowed for a single value of a log record."""

""""############### just logging config #######################"""

VERBOSE = os.environ.get("VERBOSE", "verbose_off_by_default") == "1"

INFO_PERIOD = int(os.environ.get("INFO_PERIOD", 12.0))
"""Seconds between rate info logging."""

WARN_TOO_MANY_MESSAGES = int(os.environ.get("WARN_TOO_MANY_MESSAGES", 20_000))
"""The size to warn that there are too many messages in the queue."""


logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)
if VERBOSE:
    logger.setLevel(logging.DEBUG)


def _log_credentials(cred):
    if hasattr(cred, "signer_email"):
        logger.info(f"Credentials: email: {cred.signer_email} type {type(cred)}")
    else:
        logger.info(f"Credentials: type {type(cred)}")


def status_to_severity(status: int):
    if not status:
        return "ERROR"
    if status < 400:
        return "INFO"
    if status < 500:
        return "WARNING"
    return "ERROR"


def truncate(value):
    if value is None:
        return ""
    out_value = str(value)
    if len(out_value) > MAX_BYTES_PER_VALUE:
        return out_value[:MAX_BYTES_PER_VALUE-11] + "-TRUNCATED"
    else:
        return out_value


def to_gcp_log_item(message: Message) -> Tuple[dict,dict]:
    """The format of the message from Fastly is not too important.

    It MUST have a timestamp in Y-M-DTH:M:S+0000 format.

    All other values will be added as key values pairs to the `jsonPayload`
    """
    try:
        data: dict = json.loads(message.data.decode('utf-8').strip())
        return (
            {key: truncate(value) for key, value in data.items() if key != "timestamp"},
            {
                "severity": status_to_severity(data.get("status", 500)),
                # This cause the log line to show up in GCP at the date of the original http request
                "timestamp": datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S%z"),
                "resource": Resource(type="generic_node",
                                     labels={"project_id": PROJECT_ID,
                                             "namespace": "fastly",
                                             "node_id": data.get("fastly_server", "server_unknown")})
            }
        )
    except Exception:
        logger.exception("Problem converting message to log item, skipping")
        return {}, {}


WorkItem = Tuple[Message, float]
"""An item of work which is a Pub/Sub message and an arrival time."""


RUN = True
"""Global used to force threads to stop."""

shared_messages: deque[WorkItem] = deque()  # thread safe, left side: oldest, right newest.
msg_rate = Rate(plural_noun="pub/sub messages")  # thread safe
log_write_rate = Rate(plural_noun=f"log entries written to GCP")
cv = Condition()  # Used only for notification waiting log_to_gcp threads
monitor_cv = Condition()  # Only used to wake the monitor thread at shutdown
streaming_pull_future = None


def orderly_shutdown(signum, frame):
    global RUN
    RUN = False
    global streaming_pull_future
    if streaming_pull_future:
        streaming_pull_future.cancel()
        streaming_pull_future.result()
    with cv:
        cv.notify_all()
    with monitor_cv:
        monitor_cv.notify_all()


signal.signal(signal.SIGINT, orderly_shutdown)
signal.signal(signal.SIGTERM, orderly_shutdown)


def log_to_gcp():
    """Function for thread that reads from `shared_messages` and sends them to GCP logging API."""
    logging.debug("About to get GCP logging client.")
    log_client = gcp_logging.Client(project=PROJECT_ID)
    fastly_logger = log_client.logger(name=LOGGER_NAME)
    logging.debug("Got logging_v2 client.")

    while RUN:
        try:
            work_items: List[WorkItem] = []
            with cv:
                cv.wait_for(lambda: (len(shared_messages) and (
                        len(shared_messages) > PREFERRED_PER_BATCH
                        or shared_messages[0][1] and (perf_counter() - shared_messages[0][1]) > SEND_PERIOD)),
                        timeout=1.0)
                try:
                    [work_items.append(shared_messages.popleft()) for _ in range(MAX_PER_BATCH)]
                except IndexError:
                    pass  # ran out of messages, not a problem

            if work_items:
                messages = (to_gcp_log_item(message) for message, _ in work_items)
                with fastly_logger.batch() as batch:
                    [batch.log_struct(info=info, **kv) for info, kv in messages if info and kv]

                aki = 0
                for item in work_items:
                    item[0].ack()
                    aki += 1

                log_write_rate.event(quantity=len(work_items))
                logger.debug("Acked %d pubsub messages", aki)
        except Exception:
            logger.exception("Exception in the write-logs-to-gcp loop")
    logger.info("Worker finished orderly shutdown.")


def receive_pubsub_callback(message: Message) -> None:
    arrival = perf_counter()
    shared_messages.append((message, arrival))
    msg_rate.event()


def monitor() -> None:
    while RUN:
        try:
            with monitor_cv:
                monitor_cv.wait(timeout=SEND_PERIOD)
            logger.info(msg_rate.rate_msg())
            logger.info(log_write_rate.rate_msg())
            queue_size = len(shared_messages)
            if queue_size > WARN_TOO_MANY_MESSAGES:
                logger.warning(f"shared_messages size getting unusually large: {queue_size} messages")
        except Exception:
            logger.exception("Exception in monitor thread")


if __name__ == "__main__":
    credentials, project = google.auth.default()
    logger.info("GOOGLE_APPLICATION_CREDENTIALS envvar:" f"{os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '(not set)')}")
    _log_credentials(credentials)
    logger.info("about to start logging threads")
    threads = [Thread(target=monitor)] + [Thread(target=log_to_gcp) for _ in range(THREADS)]
    [t.start() for t in threads]
    logger.info(f"Started {THREADS} log writer threads and one monitor thread.")

    """>>>>>>>> Setup of streaming pull from Pub/Sub <<<<<<<<"""

    subscriber = pubsub_v1.SubscriberClient()
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=receive_pubsub_callback)
    logger.info(f"Listening for pub/sub messages on {subscription_path}..\n")
    with subscriber:
        try:
            streaming_pull_future.result(timeout=None)
        except Exception as ex:
            RUN = False
            logger.error("Error with pub/sub subscription", exc_info=ex)
            if isinstance(ex, PermissionDenied):
                _log_credentials(credentials)
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.

    """>>>>>>>> End of setup of streaming pull from Pub/Sub <<<<<<<<"""

    RUN = False
    logger.info("Shutting down, waiting to join thread(s)")
    [t.join() for t in threads]
    msg_rate.rate_msg()
    logger.info("Shut down, threads done.")
