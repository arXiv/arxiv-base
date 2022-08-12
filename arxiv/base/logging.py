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

from arxiv.base.globals import get_application_config


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
    config = get_application_config()

    # TODO config logging with file
    # as described here https://docs.python.org/3/howto/logging.html#configuring-logging

    # # Set the log level from the Flask app configuration.
    level = int(config.get('LOGLEVEL', logging.INFO))
    logger.setLevel(level)

    # Log messages should be in Eastern local time, for consistency with
    # classic CUL/Apache logs.
    tz = timezone(config.get('ARXIV_BUSINESS_TZ', 'US/Eastern'))
    logging.Formatter.converter = lambda *args: datetime.now(tz=tz).timetuple()

    fmt = ("application %(asctime)s - %(name)s"
           " - %(levelname)s: \"%(message)s\"")
    datefmt = '%d/%b/%Y:%H:%M:%S %z'    # Used to format asctime.
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.handlers = []    # Clear default handler(s).
    logger.addHandler(handler)
    return logger
