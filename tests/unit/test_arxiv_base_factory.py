from unittest import TestCase
from flask import Flask
from arxiv.base.factory import create_web_app


class TestBaseAppFactory(TestCase):
    """Tests for :mod:`arxiv.base.factory`."""

    def test_create_web_app(self):
        """:func:`.create_web_app` generates a :class:`.Flask` instance."""

        app = create_web_app()
        self.assertIsInstance(app, Flask)
