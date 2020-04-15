"""
Provides a logger factory with reasonable defaults.

We need to be able to analyze application logs in a consistent way across all
arXiv services. This module provides a :func:`.getLogger`, which works just
like the builtin logging.getLogger, but with a simpler interface:
``getLogger(name: str, stream: IO)``.

It sets some defaults that should be applied consistently across all arXiv
services (e.g. date formatting, overall message structure), so that we can
parse application log messages in a consistent way.
"""
from typing import IO
import logging
import sys
from datetime import datetime
from pytz import timezone, utc

from flask import request

from arxiv.base.globals import get_application_config


class RequestFormatter(logging.Formatter):
    """Logging formatter that adds the current request ID to the log record."""

    def format(self, record: logging.LogRecord) -> str:
        """Attach the request ID from the request environ to the log record."""
        try:
            request_id = request.environ.get('REQUEST_ID', None)
        except RuntimeError:
            request_id = None
        record.requestid = request_id   # type: ignore
        if 'paperid' not in record.__dict__:
            record.paperid = 'null'     # type: ignore
        return super().format(record)


def getLogger(name: str, stream: IO = sys.stderr) -> logging.Logger:
    """
    Wrapper for :func:`logging.getLogger` that applies configuration.

    Parameters
    ----------
    name : str

    Returns
    -------
    :class:`logging.Logger`
    """
    logger = logging.getLogger(name)
    # logger.propagate = False
    config = get_application_config()

    # Set the log level from the Flask app configuration.
    level = int(config.get('LOGLEVEL', logging.INFO))
    logger.setLevel(level)

    # Log messages should be in Eastern local time, for consistency with
    # classic CUL/Apache logs.
    tz = timezone(config.get('ARXIV_BUSINESS_TZ', 'US/Eastern'))
    logging.Formatter.converter = lambda *args: datetime.now(tz=tz).timetuple()

    # Set the formats for log messages and asctime. We instantiate our own
    # StreamHandler so that we can use RequestFormatter (above).
    fmt = ("application %(asctime)s - %(name)s - %(requestid)s"
           " - [arxiv:%(paperid)s] - %(levelname)s: \"%(message)s\"")
    datefmt = '%d/%b/%Y:%H:%M:%S %z'    # Used to format asctime.
    handler = logging.StreamHandler(stream)
    handler.setFormatter(RequestFormatter(fmt=fmt, datefmt=datefmt))
    logger.handlers = []    # Clear default handler(s).
    logger.addHandler(handler)
    return logger
