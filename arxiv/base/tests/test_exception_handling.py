from unittest import TestCase
from flask import Flask

from http import HTTPStatus as status
from arxiv.base import Base
from arxiv.base.factory import create_web_app


class TestExceptionHandling(TestCase):
    """HTTPExceptions should be handled with custom templates."""

    def setUp(self):
        """Initialize an app and install :class:`.Base`."""
        self.app = create_web_app()
        self.client = self.app.test_client()

    def test_401(self):
        """A 401 response should be returned."""
        response = self.client.get('/401')
        self.assertEqual(response.status_code, status.UNAUTHORIZED)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')

    def test_404(self):
        """A 404 response should be returned."""
        response = self.client.get('/404')
        self.assertEqual(response.status_code, status.NOT_FOUND)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')

    def test_400(self):
        """A 400 response should be returned."""
        response = self.client.get('/400')
        self.assertEqual(response.status_code, status.BAD_REQUEST)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')

    def test_403(self):
        """A 403 response should be returned."""
        response = self.client.get('/403')
        self.assertEqual(response.status_code, status.FORBIDDEN)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')

    def test_413(self):
        """A 413 response should be returned."""
        response = self.client.get('/413')
        self.assertEqual(response.status_code,
                         status.REQUEST_ENTITY_TOO_LARGE)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')

    def test_500(self):
        """A 500 response should be returned."""
        response = self.client.get('/500')
        self.assertEqual(response.status_code,
                         status.INTERNAL_SERVER_ERROR)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')
