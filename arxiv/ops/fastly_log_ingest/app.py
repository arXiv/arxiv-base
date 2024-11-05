"""Script to subscribe to fastly pub/sub messages and write to logging."""

import json
import logging
import os
import signal
import threading
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

from . import Rate

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

SHOW_PER_THREAD_RATES = bool(os.environ.get("SHOW_PER_THREAD_RATES", "off_by_default")) == "1"
"""Whether to show the log messages about per thread rates."""

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
        logger.exception("Problem converting message to log item")
        return {}, {}


WorkItem = Tuple[Message, float]
"""An item of work which is a Pub/Sub message and an arrival time."""


RUN = True
"""Global used to force threads to stop."""

shared_messages: deque[WorkItem] = deque()  # thread safe, left side: oldest, right newest.
msg_rate = Rate(plural_noun="pub/sub messages")  # thread safe
last_pubsub_info = perf_counter()  # only incremented and only by assignment
cv = Condition()  # Used only for notification waiting log_to_gcp threads
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


signal.signal(signal.SIGINT, orderly_shutdown)
signal.signal(signal.SIGTERM, orderly_shutdown)


def log_to_gcp():
    """Function for thread that reads from `shared_messages` and sends them to GCP logging API."""
    log_write_rate = Rate(plural_noun=f"log entries by {threading.current_thread().name}")
    last_info_msg = perf_counter()

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

                logger.debug("Acked %d pubsub messages", aki)
                if SHOW_PER_THREAD_RATES:
                    log_write_rate.event(quantity=len(work_items))

                if SHOW_PER_THREAD_RATES:
                    now = perf_counter()
                    if now - last_info_msg >= INFO_PERIOD:
                        last_info_msg = now
                        logger.info(log_write_rate.rate_msg())
        except Exception:
            logger.exception("Exception in the write-logs-to-gcp loop")
    if SHOW_PER_THREAD_RATES:
        logger.info(log_write_rate.rate_msg())  # on exit
    logger.info("Worker finished orderly shutdown.")


def _pubsub_callback(message: Message) -> None:
    global last_pubsub_info
    arrival = perf_counter()
    shared_messages.append((message, arrival))
    msg_rate.event()

    # with cv:
    #     cv.notify()

    if arrival - last_pubsub_info > INFO_PERIOD:
        last_pubsub_info = arrival
        logger.info(msg_rate.rate_msg())


if __name__ == "__main__":
    credentials, project = google.auth.default()
    logger.info("GOOGLE_APPLICATION_CREDENTIALS envvar:" f"{os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '(not set)')}")
    _log_credentials(credentials)
    logger.info("about to start logging threads")
    threads = []
    for _ in range(0, THREADS):
        threads.append(Thread(target=log_to_gcp))
    [t.start() for t in threads]
    logger.info(f"Started {len(threads)} log writer threads.")
    """>>>>>>>> Setup of streaming pull from Pub/Sub <<<<<<<<"""

    subscriber = pubsub_v1.SubscriberClient()
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=_pubsub_callback)
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
