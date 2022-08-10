"""Tests for :mod:`arxiv.base.urls`."""

from unittest import TestCase, mock
from flask import Flask, url_for, Blueprint
from arxiv.base import urls, Base
from arxiv.base.exceptions import ConfigurationError
from werkzeug.routing import BuildError


class TestStaticURLs(TestCase):
    """Test building static URLs."""

    def test_static_urls(self):
        """We have vanilla Flask app with a blueprint."""
        self.app = Flask('test')
        self.app.config['SERVER_NAME'] = 'nope.com'
        Base(self.app)

        self.app.register_blueprint(Blueprint('fooprint', __name__,
                                              url_prefix='/foo',
                                              static_folder='static',
                                              static_url_path='baz'))

        with self.app.app_context():
            url = url_for('base.static', filename='css/abs.css')
            self.assertTrue(url.startswith('http://nope.com/static/base/'))
            url = url_for('fooprint.static', filename='img/foo.jpg')
            self.assertTrue(url.startswith('http://nope.com/foo/static/test/'))

    def test_relative_static_urls(self):
        """Relative static paths are enabled."""
        self.app = Flask('test')
        self.app.config['SERVER_NAME'] = 'nope.com'
        self.app.config.update({
            'SITE_HUMAN_NAME': 'The test site of testiness',
            'SITE_HUMAN_SHORT_NAME': 'Test site',
            'RELATIVE_STATIC_PATHS': True,
            'RELATIVE_STATIC_PREFIX': 'oof',
            'SITE_URL_PREFIX': '/test'
        })
        Base(self.app)

        self.app.register_blueprint(Blueprint('fooprint', __name__,
                                              url_prefix='/foo',
                                              static_folder='static',
                                              static_url_path='baz'))

        with self.app.app_context():
            url = url_for('base.static', filename='css/abs.css')
            self.assertTrue(url.startswith('http://nope.com/oof/static/base/'),
                            'The static URL for base starts with the'
                            ' configured prefix.')
            url = url_for('fooprint.static', filename='img/foo.jpg')
            self.assertFalse(url.startswith('http://nope.com/oof'),
                             'The blueprint static path is not affected.')


class TestGetURLMap(TestCase):
    """Tests for :func:`arxiv.base.urls.get_url_map`."""

    @mock.patch('arxiv.base.urls.base_config', mock.MagicMock(URLS=[]))
    def test_no_urls_configured(self):
        """No external URLs are defined on the current app nor in base."""
        app = mock.MagicMock(config={'URLS': []})
        adapter = urls.build_adapter(app)
        self.assertEqual(len(adapter.map._rules), 0,
                         "No URL patterns are loaded")

    @mock.patch('arxiv.base.urls.base_config',
                mock.MagicMock(URLS=[
                    ('foo', '/foo', 'foo.org'),
                    ('bar', '/bar/<string:foo>', 'bar.org'),
                ]))
    def test_base_urls(self):
        """Only URLs are defined in base; the current app has none."""
        app = mock.MagicMock(config={'URLS': []})
        adapter = urls.build_adapter(app)
        self.assertEqual(len(adapter.map._rules), 2,
                         "Only base URLs are loaded")

    @mock.patch('arxiv.base.urls.base_config',
                mock.MagicMock(URLS=[
                    ('foo', '/foo', 'foo.org'),
                    ('bar', '/bar/<string:foo>', 'bar.org'),
                ]))
    def test_combined_urls(self):
        """Only non-overlapping URLs are defined in base and the app."""
        app = mock.MagicMock(config={
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        })
        adapter = urls.build_adapter(app)
        self.assertEqual(len(adapter.map._rules), 4, "All URLs are loaded")

    @mock.patch('arxiv.base.urls.base_config', mock.MagicMock(URLS=[
                    ('baz', '/foo', 'foo.org'),
                    ('bar', '/bar/<string:foo>', 'bar.org'),
                ]))
    def test_overlapping_urls(self):
        """Overlapping URLs are defined in base and the app."""
        app = mock.MagicMock(config={
            'URLS': [
                ('baz', '/baz', 'baz.org'),
                ('bat', '/bat/<string:foo>', 'bat.org'),
            ]
        })
        adapter = urls.build_adapter(app)
        self.assertEqual(len(adapter.map._rules), 3,
                         "Duplicate URLs not added")
        self.assertEqual(adapter.build('baz'), 'https://baz.org/baz',
                         "The application config is preferred to base")


class TestExternalURLFallback(TestCase):
    """Test external URL building in a Flask app."""

    def setUp(self):
        """Create a Flask app."""
        self.app = Flask('test')
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
        Base(self.app)
        with self.app.app_context():
            self.assertEqual(url_for('something'), 'http://nope.com/something')

    @mock.patch('arxiv.base.urls.base_config',
                mock.MagicMock(URLS=[
                    ('baz', '/foo', 'foo.org'),
                    ('bar', '/bar/<string:foo>', 'bar.org'),
                ]))
    def test_url_from_app_config(self):
        """url_for falls back to URLs from the application config."""
        Base(self.app)
        with self.app.app_context():
            self.assertEqual(url_for('bat', foo='yes'),
                             'https://bat.org/bat/yes')
            self.assertEqual(url_for('baz'), 'https://baz.org/baz')

    @mock.patch('arxiv.base.urls.base_config', mock.MagicMock(URLS=[
                    ('baz', '/foo', 'foo.org'),
                    ('bar', '/bar/<string:foo>', 'bar.org'),
                ]))
    def test_url_from_base_config(self):
        """url_for falls back to URLs from the application config."""
        Base(self.app)
        with self.app.app_context():
            self.assertEqual(url_for('bar', foo=1), 'https://bar.org/bar/1')


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

        @self.app.route('/acknowledgment_location')
        def acknowledgment_location():
            return url_for('acknowledgment')

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
        self.assertEqual(self.client.get('/acknowledgment_location').data,
                         b'https://arxiv.org/about/ourmembers')
