"""Tests for :mod:`arxiv.base.urls`."""

from unittest import TestCase, mock
from flask import Flask
from arxiv.base.urls import config_url
from arxiv.base.exceptions import ConfigurationError


class TestConfigURL(TestCase):
    """Tests for :func:`arxiv.base.urls.config_url`."""

    def test_config_url_key_exists(self):
        """config_url() is called for an URL that is configured on the app."""
        app = Flask('foo')
        app.config['EXTERNAL_URLS'] = {
            'foo': 'https://foo.arxiv.org'
        }
        with app.app_context():
            url = config_url('foo')

        self.assertEqual(url, 'https://foo.arxiv.org',
                         "Should return configured URL")

    @mock.patch('base.urls.config')
    def test_config_url_key_not_on_current_app(self, mock_base_config):
        """config_url() is called for an URL that is not on the current app."""
        mock_base_config.EXTERNAL_URLS = {}
        mock_base_config.EXTERNAL_URLS['foo'] = 'https://bar.arxiv.org'
        app = Flask('foo')
        with app.app_context():
            url = config_url('foo')

        self.assertEqual(url, 'https://bar.arxiv.org',
                         "Should return URL configured in arxiv base")

    @mock.patch('base.urls.config')
    def test_config_url_key_not_set_anywhere(self, mock_base_config):
        """config_url() is called for an URL that is not configured."""
        app = Flask('foo')
        mock_base_config.EXTERNAL_URLS = {}
        with app.app_context():
            with self.assertRaises(ConfigurationError):
                config_url('foo')

    @mock.patch('base.urls.config')
    def test_config_url_with_format_parameter(self, mock_base_config):
        """URL requires a parameter, which is provided."""
        mock_base_config.EXTERNAL_URLS = {
            'foo': 'https://bar.arxiv.org/{foo}'
        }
        app = Flask('foo')
        with app.app_context():
            url = config_url('foo', {'foo': 'bar'})

        self.assertEqual(url, 'https://bar.arxiv.org/bar',
                         "Should return URL configured in arxiv base")

    @mock.patch('base.urls.config')
    def test_config_url_with_parameter_not_provided(self, mock_base_config):
        """URL requires a parameter, which is not provided."""
        mock_base_config.EXTERNAL_URLS = {
            'foo': 'https://bar.arxiv.org/{foo}'
        }
        app = Flask('foo')
        with app.app_context():
            with self.assertRaises(ValueError):
                config_url('foo')

    def test_config_url_with_get_param(self):
        """Request parameters are included."""
        app = Flask('foo')
        app.config['EXTERNAL_URLS'] = {
            'foo': 'https://foo.arxiv.org'
        }
        with app.app_context():
            url = config_url('foo', params={'baz': 'bat'})

        self.assertEqual(url, 'https://foo.arxiv.org?baz=bat',
                         "Should return configured URL")

    def test_config_url_with_extra_get_param(self):
        """Request parameters are included in addition to those present."""
        app = Flask('foo')
        app.config['EXTERNAL_URLS'] = {
            'foo': 'https://foo.arxiv.org?yes=no'
        }
        with app.app_context():
            url = config_url('foo', params={'baz': 'bat'})

        self.assertEqual(url, 'https://foo.arxiv.org?baz=bat&yes=no',
                         "Should return configured URL")
