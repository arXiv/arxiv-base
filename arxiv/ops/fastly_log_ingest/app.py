"""Script to subscribe to fastly pub/sub messages and write to logging."""
import json
import os
from collections import deque
from threading import Lock, Thread
import logging

from concurrent.futures import TimeoutError
from time import perf_counter
from typing import List

from google.api_core.exceptions import PermissionDenied
from google.cloud import pubsub_v1, logging_v2
import google.auth
from google.cloud.pubsub_v1.subscriber.message import Message
from arxiv.ops.fastly_log_ingest import logs_to_gcp, to_log_entry, Rate

credentials, project = google.auth.default()

PROJECT_ID = os.environ.get("PROJECT_ID", "arxiv-production")
SUBSCRIPTION_ID = os.environ.get("SUBSCRIPTION_ID", "logs-fastly-arxiv-org-sub")

VERBOSE = os.environ.get("VERBOSE", "1") == "1"
THREADS = int(os.environ.get("THREADS", 1))  # threads to send logs
SEND_PERIOD = int(os.environ.get("SEND_PERIOD", 8.0))  # seconds to wait for messages to accumulate
INFO_PERIOD = int(os.environ.get("INFO_PERIOD", 20.0))  # seconds between info logging

"""Number of log records in a batch.
GCP Logging limits (https://cloud.google.com/logging/quotas#api-limits) say 10MB as of 2023-11.
If we guess an average of 1024 bytes per message, 2048 entries would be 2MB. 
"""
MAX_PER_BATCH = int(os.environ.get("MAX_PER_BATCH", 2048))

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WorkItem:
    """An item of work which is a Pub/Sub message and an arrival time."""

    def __init__(self, message: Message, arrival_time: float):
        self.message = message
        self.arrival_time = arrival_time

    def to_log_entry(self) -> dict:
        """Extracts the JSON to a python dict from the Pub/Sub message."""
        return to_log_entry(json.loads(self.message.data.decode('utf-8').strip()))


RUN = True

shared_messages: deque[WorkItem] = deque()
msg_rate = Rate(plural_noun="pub/sub messages")
last_pubsub_info = perf_counter()
lock = Lock()  # lock protects the above three objects


def _logging_thread():
    log_write_rate = Rate(plural_noun="log entries")
    logging.debug("About to get logging_v2 client.")
    log_client = logging_v2.Client(project=PROJECT_ID)
    logging.debug("Got logging_v2 client.")
    last_info_msg = perf_counter()
    while RUN:
        batch: List[WorkItem] = []
        lock.acquire(timeout=2.0)
        try:
            now = perf_counter()
            msg_count = len(shared_messages)
            if msg_count == 0:
                continue
            if msg_count > MAX_PER_BATCH or (now - shared_messages[0].arrival_time) > SEND_PERIOD:
                batch.extend([shared_messages.pop() for _ in range(min([msg_count, MAX_PER_BATCH]))])
        finally:
            lock.release()
        if batch:
            logger.debug(f"Got batch of %d pub/sub messages", len(batch))
            logs_to_gcp(log_client, [item.to_log_entry() for item in batch])
            logger.debug("Finished sending entries to gcp logging.")
            for item in batch:
                item.message.ack()
                logger.debug("ack pub/sub message %s", item.message.message_id)
            log_write_rate.event(quantity=len(batch))
        if perf_counter() - last_info_msg >= INFO_PERIOD:
            last_info_msg = now
            logger.info(log_write_rate.rate_msg())
        pass
    logger.info(log_write_rate.rate_msg())


def _pubsub_callback(message: Message) -> None:
    global last_pubsub_info
    arrival = perf_counter()
    with lock:
        shared_messages.append(WorkItem(message, arrival))
        logger.debug("got message %s and added to queue", message.message_id)
        msg_rate.event()
        now = perf_counter()
        if now - last_pubsub_info > INFO_PERIOD:
            last_pubsub_info = now
            logger.info(msg_rate.rate_msg())


if __name__ == "__main__":
    logger.debug("about to start logging threads")
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
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result(timeout=None)
        except Exception as ex:
            logger.error("Error with pub/sub subscription", exc_info=ex)
            if isinstance(ex, PermissionDenied):
                logger.info(f"Credentials principle: {credentials.signer_email}")
            RUN = False
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.

    """>>>>>>>> End of setup of streaming pull from Pub/Sub <<<<<<<<"""

    RUN = False
    logger.info("Shutting down, waiting to join thread(s)")
    [t.join() for t in threads]
    msg_rate.rate_msg()
    logger.info("Shut down, threads done.")

