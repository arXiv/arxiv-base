"""Script to subscribe to fastly pub/sub messages and write to logging."""
import json
import os
from collections import deque
from datetime import datetime
from threading import Condition, Thread
import logging

from time import perf_counter
from typing import List
from zoneinfo import ZoneInfo

from google.api_core.exceptions import PermissionDenied
from google.cloud import pubsub_v1, logging as gcp_logging
import google.auth
from google.cloud.logging_v2.entries import Resource
from google.cloud.pubsub_v1.subscriber.message import Message
from arxiv.ops.fastly_log_ingest import Rate

PROJECT_ID = os.environ.get("PROJECT_ID", "arxiv-production")
SUBSCRIPTION_ID = os.environ.get("SUBSCRIPTION_ID", "logs-fastly-arxiv-org-sub")

VERBOSE = os.environ.get("VERBOSE", "verbose_off_by_default") == "1"
THREADS = int(os.environ.get("THREADS", 1))  # threads to send logs
SEND_PERIOD = int(os.environ.get("SEND_PERIOD", 8.0))  # seconds to wait for messages to accumulate
INFO_PERIOD = int(os.environ.get("INFO_PERIOD", 12.0))  # seconds between info logging

LOGGER_NAME = os.environ.get("LOGGER_NAME", "fastly_log_ingest")
# name of logger in GCP, don't prefix with project-id or anything
"""Number of log records in a batch. Limit seems to be 16kb but not sure."""
MAX_PER_BATCH = int(os.environ.get("MAX_PER_BATCH", 10))

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)
if VERBOSE:
    logger.setLevel(logging.DEBUG)

utc_zone = ZoneInfo("UTC")


def _log_credentials(cred):
    if hasattr(cred, "signer_email"):
        logger.info(f"Credentials: email: {cred.signer_email} type {type(cred)}")
    else:
        logger.info(f"Credentials: type {type(cred)}")


class WorkItem:
    """An item of work which is a Pub/Sub message and an arrival time."""

    def _status_to_severity(self, status: int):
        if not status:
            return "ERROR"
        if status < 400:
            return "INFO"
        if status < 500:
            return "WARNING"
        return "ERROR"

    def __init__(self, message: Message, arrival_time: float):
        self.message = message
        self.arrival_time = arrival_time
        try:
            self.data: dict = json.loads(message.data.decode('utf-8').strip())
        except Exception as e:
            logger.warning(f'Failed to log the following message: {message.data.decode("utf-8", errors='replace')} with {str(e)}')

    def to_payload(self) -> dict:
        """Convert the message into a `payload` for the log entry."""
        return {key: value for key, value in self.data.items() if key != "timestamp"}

    def to_metadata(self) -> dict:
        """Convert the message into the metadata the log entry.

        Seting `timestamp` here causes the time of the log line to be the time
        of the original http request instead of the time of the line entry into GCP.
        """
        return {
            "severity": self._status_to_severity(self.data.get("status", 500)),
            # This cause the log line to show up in GCP at the date of the original http request
            "timestamp": datetime.strptime(self.data["timestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=utc_zone),
            "resource": Resource(type="generic_node",
                                 labels={"project_id": PROJECT_ID,
                                         "namespace": "fastly",
                                         "node_id": self.data.get("fastly_server", "server_unknown")})

        }


RUN = True

shared_messages: deque[WorkItem] = deque()
msg_rate = Rate(plural_noun="pub/sub messages")
last_pubsub_info = perf_counter()
cv = Condition()  # lock protects the above three objects


def _logging_thread():
    log_write_rate = Rate(plural_noun="log entries")
    logging.info("About to get logging_v2 client.")
    log_client = gcp_logging.Client(project=PROJECT_ID)
    fastly_logger = log_client.logger(name=LOGGER_NAME)

    logging.info("Got logging_v2 client.")
    last_info_msg = perf_counter()
    while RUN:
        work_items: List[WorkItem] = []
        with cv:
            cv.wait_for(lambda: shared_messages, timeout=2.0)  # timeout to allow exit or periodic message
            now = perf_counter()
            msg_count = len(shared_messages)
            if msg_count and (msg_count > MAX_PER_BATCH or (now - shared_messages[0].arrival_time) > SEND_PERIOD):
                work_items.extend([shared_messages.pop() for _ in range(min([msg_count, MAX_PER_BATCH]))])

        if work_items:
            logger.debug("About to log batch of %d pub/sub messages", len(work_items))
            log_items = []
            for item in work_items:
                try:
                    log_items.append((item.to_payload(), item.to_metadata()))
                except Exception as exc:
                    logger.error("Skipping line, problem while converting log line", exc)

            with fastly_logger.batch() as batch:
                [batch.log_struct(info=info, **kv) for info, kv in log_items]

            aki = 0
            for item in work_items:
                item.message.ack()
                aki += 1

            logger.debug("Acked %d pubsub messages", aki)
            log_write_rate.event(quantity=len(work_items))
        now = perf_counter()
        if now - last_info_msg >= INFO_PERIOD:
            last_info_msg = now
            logger.info(log_write_rate.rate_msg())
    logger.info(log_write_rate.rate_msg())  # on exit


def _pubsub_callback(message: Message) -> None:
    global last_pubsub_info
    arrival = perf_counter()
    with cv:
        shared_messages.append(WorkItem(message, arrival))
        msg_rate.event()
        now = perf_counter()
        if now - last_pubsub_info > INFO_PERIOD:
            last_pubsub_info = now
            logger.info(msg_rate.rate_msg())


if __name__ == "__main__":
    credentials, project = google.auth.default()
    logger.info("GOOGLE_APPLICATION_CREDENTIALS envvar:"
                f"{os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '(not set)')}")
    _log_credentials(credentials)
    logger.info("about to start logging threads")
    threads = []
    for _ in range(0, THREADS):
        threads.append(Thread(target=_logging_thread))
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
