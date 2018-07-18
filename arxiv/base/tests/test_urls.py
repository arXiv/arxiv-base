"""Tests for :mod:`arxiv.base.urls`."""

from unittest import TestCase, mock
from flask import Flask, url_for
from arxiv.base import urls, Base
from arxiv.base.exceptions import ConfigurationError
from werkzeug.routing import BuildError


class TestGetURLMap(TestCase):
    """Tests for :func:`arxiv.base.urls.get_url_map`."""

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_no_urls_configured(self, mock_current_app, mock_base_config):
        """No external URLs are defined on the current app nor in base."""
        mock_current_app.config = {
            'URLS': []
        }
        mock_base_config.URLS = []
        url_map = urls.get_url_map()
        self.assertEqual(len(url_map._rules), 0, "No URL patterns are loaded")

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_base_urls(self, mock_current_app, mock_base_config):
        """Only URLs are defined in base; the current app has none."""
        mock_current_app.config = {
            'URLS': []
        }
        mock_base_config.URLS = [
            ('foo', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        url_map = urls.get_url_map()
        self.assertEqual(len(url_map._rules), 2, "Only base URLs are loaded")

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_combined_urls(self, mock_current_app, mock_base_config):
        """Only non-overlapping URLs are defined in base and the app."""
        mock_current_app.config = {
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        }
        mock_base_config.URLS = [
            ('foo', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        url_map = urls.get_url_map()
        self.assertEqual(len(url_map._rules), 4, "All URLs are loaded")

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_overlapping_urls(self, mock_current_app, mock_base_config):
        """Overlapping URLs are defined in base and the app."""
        mock_current_app.config = {
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        }
        mock_base_config.URLS = [
            ('baz', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        url_map = urls.get_url_map()
        self.assertEqual(len(url_map._rules), 3, "Duplicate URLs not added")
        adapter = url_map.bind('nope.com', url_scheme='https')
        self.assertEqual(adapter.build('baz'), 'https://baz.org/baz',
                         "The application config is preferred to base")


class TestExternalURLFor(TestCase):
    """Tests for :func:`arxiv.base.urls.external_url_for`."""

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_no_urls_configured(self, mock_current_app, mock_base_config):
        """No external URLs are defined on the current app nor in base."""
        mock_current_app.config = {
            'URLS': []
        }
        mock_base_config.URLS = []
        with self.assertRaises(BuildError):
            urls.external_url_for('foo')

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_base_urls(self, mock_current_app, mock_base_config):
        """Only URLs are defined in base; the current app has none."""
        mock_current_app.config = {
            'URLS': []
        }
        mock_base_config.URLS = [
            ('foo', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        self.assertEqual(urls.external_url_for('foo'), 'https://foo.org/foo')
        self.assertEqual(urls.external_url_for('bar', foo=1),
                         'https://bar.org/bar/1')

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_combined_urls(self, mock_current_app, mock_base_config):
        """Only non-overlapping URLs are defined in base and the app."""
        mock_current_app.config = {
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        }
        mock_base_config.URLS = [
            ('foo', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        self.assertEqual(urls.external_url_for('foo'), 'https://foo.org/foo')
        self.assertEqual(urls.external_url_for('baz'), 'https://baz.org/baz')
        self.assertEqual(urls.external_url_for('bar', foo=1),
                         'https://bar.org/bar/1')
        self.assertEqual(urls.external_url_for('bat', foo='yes'),
                         'https://bat.org/bat/yes')

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_overlapping_urls(self, mock_current_app, mock_base_config):
        """Overlapping URLs are defined in base and the app."""
        mock_current_app.config = {
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        }
        mock_base_config.URLS = [
            ('baz', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        self.assertEqual(urls.external_url_for('baz'), 'https://baz.org/baz')
        self.assertEqual(urls.external_url_for('bar', foo=1),
                         'https://bar.org/bar/1')
        self.assertEqual(urls.external_url_for('bat', foo='yes'),
                         'https://bat.org/bat/yes')


class TestExternalURLFallback(TestCase):
    """Test external URL building in a Flask app."""

    def setUp(self):
        """Create a Flask app."""
        self.app = Flask('test')
        Base(self.app)
        self.app.config['URLS'] = [
            ('baz', '/baz', 'baz.org'),
            ('bat', '/bat/<string:foo>', 'bat.org'),
        ]
        self.app.config['SERVER_NAME'] = 'nope.com'

        @self.app.route('/something')
        def something():
            return 'nothing'

    def test_application_url(self):
        """url_for works as expected for an app-defined URL."""
        with self.app.app_context():
            self.assertEqual(url_for('something'), 'http://nope.com/something')

    @mock.patch('arxiv.base.urls.config')
    def test_url_from_app_config(self, mock_base_config):
        """url_for falls back to URLs from the application config."""
        mock_base_config.URLS = [
            ('baz', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        with self.app.app_context():
            self.assertEqual(url_for('bat', foo='yes'),
                             'https://bat.org/bat/yes')
            self.assertEqual(url_for('baz'), 'https://baz.org/baz')

    @mock.patch('arxiv.base.urls.config')
    def test_url_from_base_config(self, mock_base_config):
        """url_for falls back to URLs from the application config."""
        mock_base_config.URLS = [
            ('baz', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        with self.app.app_context():
            self.assertEqual(url_for('bar', foo=1), 'https://bar.org/bar/1')


class TestExternalURLFor(TestCase):
    """Tests for :func:`arxiv.base.urls.external_url_for`."""

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_no_urls_configured(self, mock_current_app, mock_base_config):
        """No external URLs are defined on the current app nor in base."""
        mock_current_app.config = {
            'URLS': []
        }
        mock_base_config.URLS = []
        with self.assertRaises(BuildError):
            urls.external_url_for('foo')

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_base_urls(self, mock_current_app, mock_base_config):
        """Only URLs are defined in base; the current app has none."""
        mock_current_app.config = {
            'URLS': []
        }
        mock_base_config.URLS = [
            ('foo', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        self.assertEqual(urls.external_url_for('foo'), 'https://foo.org/foo')
        self.assertEqual(urls.external_url_for('bar', foo=1),
                         'https://bar.org/bar/1')

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_combined_urls(self, mock_current_app, mock_base_config):
        """Only non-overlapping URLs are defined in base and the app."""
        mock_current_app.config = {
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        }
        mock_base_config.URLS = [
            ('foo', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        self.assertEqual(urls.external_url_for('foo'), 'https://foo.org/foo')
        self.assertEqual(urls.external_url_for('baz'), 'https://baz.org/baz')
        self.assertEqual(urls.external_url_for('bar', foo=1),
                         'https://bar.org/bar/1')
        self.assertEqual(urls.external_url_for('bat', foo='yes'),
                         'https://bat.org/bat/yes')

    @mock.patch('arxiv.base.urls.config')
    @mock.patch('arxiv.base.urls.current_app')
    def test_overlapping_urls(self, mock_current_app, mock_base_config):
        """Overlapping URLs are defined in base and the app."""
        mock_current_app.config = {
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        }
        mock_base_config.URLS = [
            ('baz', '/foo', 'foo.org'),
            ('bar', '/bar/<string:foo>', 'bar.org'),
        ]
        self.assertEqual(urls.external_url_for('baz'), 'https://baz.org/baz')
        self.assertEqual(urls.external_url_for('bar', foo=1),
                         'https://bar.org/bar/1')
        self.assertEqual(urls.external_url_for('bat', foo='yes'),
                         'https://bat.org/bat/yes')


class TestWithClient(TestCase):
    """Test external URL building in a Flask app."""

    def setUp(self):
        """Create a Flask app."""
        self.app = Flask('test')
        self.app.config['URLS'] = [
            ('baz', '/baz', 'baz.org'),
            ('bat', '/bat/<string:foo>', 'bat.org'),
        ]
        self.app.config['SERVER_NAME'] = 'nope.com'
        Base(self.app)

        @self.app.route('/baz_location')
        def baz_location():
            return url_for('baz')

        @self.app.route('/bat_location')
        def bat_location():
            return url_for('bat', foo=1)

        @self.app.route('/something')
        def something():
            return 'nothing'

        self.client = self.app.test_client()

    def test_application_url(self):
        """url_for works as expected for an app-defined URL."""
        self.assertEqual(self.client.get('/baz_location').data,
                         b'https://baz.org/baz')
        self.assertEqual(self.client.get('/bat_location').data,
                         b'https://bat.org/bat/1')
