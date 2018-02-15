"""Tests for :mod:`arxiv.base.context_processors`."""

from unittest import TestCase, mock
from flask import Flask

from arxiv.base.context_processors import config_url_builder
from arxiv.base.exceptions import ConfigurationError


class TestConfigURLBuilderContextProcessor(TestCase):
    """config_url_builder() injects a URL factory into the response context."""

    def test_config_url_builder_returns_a_function(self):
        """config_url_builder() should return a dict with config_url()."""
        extra_context = config_url_builder()
        self.assertIsInstance(extra_context, dict, "Should return a dict")
        self.assertIn('config_url', extra_context,
                      "Should contain `config_url` key")
        self.assertTrue(hasattr(extra_context['config_url'], '__call__'),
                        "Value for ``config_url`` should be callable.")

    def test_config_url_key_exists(self):
        """config_url() is called for an URL that is configured on the app."""
        app = Flask('foo')
        app.config['ARXIV_FOO_URL'] = 'https://foo.arxiv.org'
        with app.app_context():
            extra_context = config_url_builder()
            config_url = extra_context['config_url']
            url = config_url('foo')

        self.assertEqual(url, app.config['ARXIV_FOO_URL'],
                         "Should return configured URL")

    @mock.patch('arxiv.base.context_processors.config')
    def test_config_url_key_not_on_current_app(self, mock_base_config):
        """config_url() is called for an URL that is not on the current app."""
        mock_base_config.ARXIV_FOO_URL = 'https://bar.arxiv.org'
        app = Flask('foo')
        with app.app_context():
            extra_context = config_url_builder()
            config_url = extra_context['config_url']
            url = config_url('foo')

        self.assertEqual(url, 'https://bar.arxiv.org',
                         "Should return URL configured in arxiv base ")

    def test_config_url_key_not_set_anywhere(self):
        """config_url() is called for an URL that is not configured."""
        app = Flask('foo')
        with app.app_context():
            extra_context = config_url_builder()
            config_url = extra_context['config_url']
            with self.assertRaises(ConfigurationError):
                config_url('foo')
