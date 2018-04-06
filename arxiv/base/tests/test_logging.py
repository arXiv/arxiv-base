from unittest import TestCase, mock
import sys
from contextlib import contextmanager
from io import StringIO

import logging as pyLogging
from arxiv.base import logging


class TestGetLogger(TestCase):
    """Test :func:`.logging.getLogger`."""

    def test_get_logger_no_app_nor_request(self):
        """There is no application nor request context."""
        stream = StringIO()

        logger = logging.getLogger('foologger', stream)
        self.assertIsInstance(logger, pyLogging.Logger,
                              "Should return a logging.Logger instance")

        logger.error('foo')
        captured_value = stream.getvalue()
        stream.close()
        self.assertIn('ERROR: "foo"', captured_value,
                      "Should log normally even if request is not present")

    @mock.patch('arxiv.base.logging.request')
    def test_get_logger_with_request(self, mock_request):
        """The request context is available."""
        mock_request.environ = {'request_id': 'foo-id-1234'}
        stream = StringIO()
        logger = logging.getLogger('foologger', stream)
        self.assertIsInstance(logger, pyLogging.Logger,
                              "Should return a logging.Logger instance")
        logger.error('foo')
        captured_value = stream.getvalue()
        stream.close()
        self.assertIn('foo-id-1234', captured_value,
                      "Should include request ID in log messages")

    @mock.patch('arxiv.base.logging.get_application_config')
    def test_config_sets_loglevel(self, mock_get_config):
        """LOGLEVEL param in config controls log level."""
        mock_get_config.return_value = {'LOGLEVEL': 10}
        stream = StringIO()
        logger = logging.getLogger('foologger', stream)
        logger.debug('foo')
        captured_value = stream.getvalue()
        stream.close()
        self.assertIn('DEBUG', captured_value,
                      "Changing LOGLEVEL in the app config should change the"
                      " logger log level")

    def test_paper_id_is_set(self):
        """``paperid`` is included in the log data."""
        stream = StringIO()
        logger = logging.getLogger('foologger', stream)
        logger.error('what', extra={'paperid': '1234'})
        captured_value = stream.getvalue()
        stream.close()
        self.assertIn('arxiv:1234', captured_value,
                      "Should include paper ID in log messages")

    def test_paper_id_is_not_set(self):
        """``paperid`` is not included in the log data."""
        stream = StringIO()
        logger = logging.getLogger('foologger', stream)
        logger.error('what')
        captured_value = stream.getvalue()
        stream.close()
        self.assertIn('arxiv:null', captured_value,
                      "Paper ID should be null in log messages")
