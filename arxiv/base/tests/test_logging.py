from unittest import TestCase
from io import StringIO

import logging as pyLogging
# CAREFUL: This does not do what you think it does:
# from arxiv.base import logging
import arxiv.base.logging


class TestGetLogger(TestCase):
    """Test :func:`.logging.getLogger`."""

    def test_get_logger_no_app_nor_request(self):
        """There is no application nor request context."""
        stream = StringIO()

        logger = arxiv.base.logging.getLogger('foologger')
        handler = pyLogging.StreamHandler(stream)
        handler.setFormatter(
            pyLogging.Formatter(
                '%(levelname)s: "%(message)s"'
            )
        )
        handler.terminator = ''
        logger.addHandler(handler)
        self.assertIsInstance(logger, pyLogging.Logger,
                              "Should return a logging.Logger instance")

        logger.error('foo')
        captured_value = stream.getvalue()
        stream.close()
        self.assertIn('ERROR: "foo"', captured_value,
                      "Should log normally even if request is not present")
