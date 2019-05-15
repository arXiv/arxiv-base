"""Tests for static URL modifications in :class:`.Base`."""

from unittest import TestCase, mock

from flask import Flask, url_for

from .. import Base


class TestAppWithStaticFiles(TestCase):
    """We are using :class:`.Base` on a Flask app."""

    def setUp(self):
        """Set up an app with static files."""
        self.static_url_path = '/a/static/path'
        self.host = 'foo.host'
        self.version = '0.3.2'
        self.app = Flask(__name__, static_url_path=self.static_url_path)
        self.app.config['APP_VERSION'] = self.version
        self.app.config['SERVER_NAME'] = self.host

    def test_base_alters_static_url(self):
        """When :class:`.Base` is applied, the static url path is changed."""
        with self.app.app_context():
            target_url = url_for('static', filename='foo.txt')

        self.assertEqual(
            target_url,
            f'http://{self.host}/a/static/path/foo.txt'
        )

        Base(self.app)

        with self.app.app_context():
            target_url = url_for('static', filename='foo.txt')

        self.assertEqual(
            target_url,
            f'http://{self.host}/static/{self.app.name}/{self.version}/foo.txt'
        )
