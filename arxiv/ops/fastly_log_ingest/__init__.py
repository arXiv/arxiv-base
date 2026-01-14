"""Script to send fastly request log pub/sub events to GCP logging.

Fastly does not offer a way to directly send reqeust logging to GCP
logging. They do offer sending files to GS, send to pub/sub, sending to
a REST endpoint and sending to BigTable.

A docker file for this is at ./deploy/Dockerfile-fastlylogingest.
"""

import math
from collections import deque
from time import perf_counter
from typing import Optional


class Rate:
    """Class to record the rate of events."""

    def __init__(self, window_sec: float = 360.0, bins: int = 20, plural_noun=""):
        self.window = window_sec
        self.window_start = perf_counter()
        self.bins = bins
        self.bin_sec = self.window / self.bins
        self.fifo: deque[float] = deque(maxlen=bins)
        self.fifo.append(0)
        self.noun = plural_noun.strip() + " "

    def event(self, at: Optional[float] = None, quantity=1):
        """Record a `quantity` of events at time `at`."""
        at = at or perf_counter()
        dt = at - self.window_start
        if dt <= self.bin_sec:
            count = self.fifo.pop()
            count = count + quantity
            self.fifo.append(count)
            return

        missing_bins = math.floor(dt / self.bin_sec)
        [self.fifo.append(0) for _ in range(missing_bins - 1)]
        self.fifo.append(quantity)
        self.window_start = perf_counter()

    def rate_msg(self):
        """Returns a rate message."""
        self.event(quantity=0)  # catch up on any missing bins
        qsize = len(self.fifo)
        if qsize == 0:
            return f"Zero {self.noun} happened"
        ave_per_bin = sum(self.fifo) / qsize
        ave_per_sec = ave_per_bin / self.bin_sec
        return f"Rate: {ave_per_sec:.2f} {self.noun}per sec over last {self.window} sec"
