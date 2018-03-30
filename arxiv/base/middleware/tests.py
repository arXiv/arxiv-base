"""Tests for :mod:`.middleware`."""

from unittest import TestCase, mock
from flask import Flask

import sys


class TestWrap(TestCase):
    """Test :func:`.middleware.wrap`."""

    def setUp(self):
        """Define a minimal request environment."""
        self.environ = {
            'SERVER_NAME': 'fooserver',
            'SERVER_PORT': '123',
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'HEAD'
        }

    def test_wrap_attaches_middleware(self):
        """:func:`.middleware.wrap` attaches WSGI middleware to a Flask app."""
        from arxiv.base import middleware

        class FooMiddleware(object):
            def __init__(self, app):
                self.app = app
                self.called = False

            def __call__(self, environ, start_response):
                self.called = True
                return self.app(environ, start_response)

            @property
            def wsgi_app(self):
                return self

        app = Flask('test')
        middleware.wrap(app, [FooMiddleware])
        self.assertIsInstance(app.wsgi_app, FooMiddleware,
                              "Middleware should be attached to Flask app")
        app(self.environ, mock.MagicMock())
        self.assertTrue(app.wsgi_app.called,
                        "Middleware should be called when Flask app is called")

    def test_wrap_is_inside_out(self):
        """Order of middleware determines call order upon request."""
        from arxiv.base import middleware

        class FirstMiddleware(middleware.base.BaseMiddleware):
            def before(self, environ, start_response):
                environ['call_order'].append('first')
                return environ, start_response

        class SecondMiddleware(middleware.base.BaseMiddleware):
            def before(self, environ, start_response):
                environ['call_order'].append('second')
                return environ, start_response

        app = Flask('test')
        self.environ['call_order'] = []
        middleware.wrap(app, [FirstMiddleware, SecondMiddleware])
        app(self.environ, mock.MagicMock())
        self.assertEqual(self.environ['call_order'][0], 'first',
                         "The first middleware should be called first")
        self.assertEqual(self.environ['call_order'][1], 'second',
                         "The second middleware should be called second")


class TestBaseMiddleware(TestCase):
    """Tests :class:`.middleware.base.BaseMiddleware`."""

    def setUp(self):
        """Define a minimal request environment."""
        self.environ = {
            'SERVER_NAME': 'fooserver',
            'SERVER_PORT': '123',
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'HEAD'
        }

    def test_base(self):
        """:class:`.BaseMiddleware` doesn't do much."""
        from arxiv.base.middleware.base import BaseMiddleware
        app = Flask('test')
        bm = BaseMiddleware(app.wsgi_app)
        app.wsgi_app = bm
        app(self.environ, mock.MagicMock())
        self.assertEqual(bm, bm.wsgi_app)


class TestRequestLogs(TestCase):
    """Tests :class:`.middleware.request_logs.ClassicLogsMiddleware`."""

    def setUp(self):
        """Define a minimal request environment."""
        self.environ = {
            'SERVER_NAME': 'fooserver',
            'SERVER_PORT': '123',
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'HEAD'
        }

    def test_uwsgi_is_available(self):
        """Attach logging middleware to app when uwsgi is available."""
        mock_uwsgi = mock.MagicMock()
        sys.modules['uwsgi'] = mock_uwsgi
        from arxiv.base.middleware import request_logs, wrap

        app = Flask('test')
        wrap(app, [request_logs.ClassicLogsMiddleware])
        self.assertIsInstance(app.wsgi_app, request_logs.ClassicLogsMiddleware,
                              "ClassicLogsMiddleware should be the outermost"
                              " middleware")
        app(self.environ, mock.MagicMock())
        self.assertGreater(mock_uwsgi.set_logvar.call_count, 0,
                           "Should set logging variables for uwsgi")

    def test_uwsgi_is_not_available(self):
        """Attach base middleware when uwsgi is not available."""
        if 'uwsgi' in sys.modules:
            del sys.modules['uwsgi']
        from arxiv.base.middleware import request_logs, wrap
        app = Flask('test')
        wrap(app, [request_logs.ClassicLogsMiddleware])
        self.assertIsInstance(app.wsgi_app, request_logs.BaseMiddleware,
                              "BaseMiddleware is attached instead")
