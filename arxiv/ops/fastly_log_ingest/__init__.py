"""
Script to send fastly request log pub/sub events to GCP logging.

Fastly does not offer a way to directly send reqeust logging to GCP logging. They do
offer sending files to GS, send to pub/sub, sending to a REST endpoint and sending to BigTable.

A docker file for this is at ./deploy/Dockerfile-fastlylogingest.
"""
from collections import deque
from time import perf_counter
from typing import Optional, Iterator, Sequence

from google.cloud import logging_v2
import logging

logger = logging.getLogger(__name__)

"""Mapping to use for resource in log entry."""
resource = {"type": "generic_node"}

"""Logger name in GCP to use for log entry."""
logger_name = "projects/arxiv-production/logs/fastly_log_ingest"


def _status_to_severity(status: int):
    if not status:
        return "ERROR"
    if status < 400:
        return "INFO"
    if status < 500:
        return "WARNING"
    return "ERROR"


def to_log_entry(req: dict):
    """Convert a `dict` to a `dict` for a GCP log entry."""
    entry = {
        "severity": _status_to_severity(req.get("status", 500)),
        "timestamp": req["timestamp"],
        "jsonPayload": req,
    }
    del req["timestamp"]
    return entry


def logs_to_gcp(client: logging_v2.Client, items: Sequence[dict]):
    """Sends log records to GCP."""
    client.logging_api.write_entries(items,
                                     resource=resource,
                                     logger_name=logger_name,
                                     partial_success=False,  # to avoid duplicates on pub/sub retry
                                     )


if __name__ == "__main__":
    log_client = logging_v2.Client(project="arxiv-production")

    """Testing this by getting a example of the pub/sub that fastly would send and
    pasting it here."""

    data = {"timestamp": "2023-11-07T21:15:59Z", "remote_addr": "67.249.88.118", "geo_country": "united states",
            "geo_city": "candor", "geo_lat": "42.200", "geo_long": "-76.320", "host": "web3.arxiv.org",
            "path": "/list/astro-ph/new", "method": "GET", "protocol": "HTTP/1.1",
            "referer": "http://web3.arxiv.org.global.prod.fastly.net/",
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "state": "PASS", "status": 200, "reason": "OK", "body_size": 102030, "fastly_server": "cache-lga21947-LGA",
            "fastly_is_edge": True, "ttfb": 0.579}

    logs_to_gcp(log_client, [to_log_entry(data)])


class Rate:
    """Class to record the rate of events."""

    def __init__(self, window_sec: float = 360.0, bins: int = 20, plural_noun=""):
        self.window = window_sec
        self.window_start = perf_counter()
        self.bins = bins
        self.bin_sec = self.window / self.bins
        self.fifo = deque(maxlen=bins)
        self.fifo.append(0)
        self.noun = plural_noun.strip() + " "

    def event(self, at: Optional[float] = None, quantity=1):
        """Record a `quantity` of events at time `at`."""
        if not at:
            at = perf_counter()

        if at > self.window_start + self.bin_sec:
            self.fifo.append(1)
        else:
            count = self.fifo.pop()
            count = count + quantity
            self.fifo.append(count)

    def rate_msg(self):
        """Returns a rate message."""
        qsize = len(self.fifo)
        if qsize == 0:
            return f"Zero {self.noun} happened"
        ave_per_bin = sum(self.fifo) / qsize
        ave_per_sec = ave_per_bin / self.bin_sec
        return f"{ave_per_sec:.4f} {self.noun}per sec over last {self.window} sec"
