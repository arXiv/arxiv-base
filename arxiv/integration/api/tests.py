"""Tests for :mod:`.integration.api`."""

from unittest import TestCase, mock
from . import service, status, exceptions

from flask import Flask


class TestHTTPIntegration(TestCase):
    """Test for :class:`.HTTPIntegration`."""

    def session(self, status_code=status.OK, method="get", json={},
                content="", headers={}):
        """Make a mock session."""
        return mock.MagicMock(**{
            method: mock.MagicMock(
                return_value=mock.MagicMock(
                    status_code=status_code,
                    json=mock.MagicMock(
                        return_value=json
                    ),
                    content=content,
                    headers=headers
                )
            )
        })

    def setUp(self):
        """Make some apps."""
        self.app_one = Flask('one')
        self.app_two = Flask('two')

    def test_init_app(self):
        """:func:`HTTPIntegration.init_app` sets config defaults."""
        service.HTTPIntegration.init_app(self.app_one)
        self.assertEqual(self.app_one.config['BASE_ENDPOINT'],
                         service.DEFAULT_ENDPOINT)
        self.assertEqual(self.app_one.config['BASE_VERIFY'],
                         service.DEFAULT_VERIFY)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_request_in_context(self, mock_Session):
        """:func:`HTTPIntegration.request` uses contextual config."""
        session_one = mock.MagicMock(
            get=mock.MagicMock(
                return_value=mock.MagicMock(status_code=status.OK)
            )
        )
        session_two = mock.MagicMock(
            get=mock.MagicMock(
                return_value=mock.MagicMock(status_code=status.OK)
            )
        )
        mock_Session.side_effect = [session_one, session_two]
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)
        self.app_two.config['BASE_ENDPOINT'] = 'https://bazservice/foo'
        service.HTTPIntegration.init_app(self.app_two)

        with self.app_one.app_context():
            service.HTTPIntegration.request('get', '/one')

        with self.app_two.app_context():
            service.HTTPIntegration.request('get', '/two')

        session_one.get.assert_called_with('https://fooservice/baz/one')
        self.assertEqual(session_one.get.call_count, 1)
        session_two.get.assert_called_with('https://bazservice/foo/two')
        self.assertEqual(session_two.get.call_count, 1)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_handles_500_series(self, mock_Session):
        """Handles 500-series response codes."""
        session_one = self.session(status.SERVICE_UNAVAILABLE)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request('get', '/one')
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.RequestFailed)
                self.assertEqual(ex.status_code,
                                 status.SERVICE_UNAVAILABLE)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_handles_unauthorized(self, mock_Session):
        """Handles 401 Unauthorized response code."""
        session_one = self.session(status.UNAUTHORIZED)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request('get', '/one')
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.RequestUnauthorized)
                self.assertEqual(ex.status_code,
                                 status.UNAUTHORIZED)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_handles_forbidden(self, mock_Session):
        """Handles 403 Forbidden response code."""
        session_one = self.session(status.FORBIDDEN)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request('get', '/one')
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.RequestForbidden)
                self.assertEqual(ex.status_code,
                                 status.FORBIDDEN)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_handles_not_found(self, mock_Session):
        """Handles 404 Not Found response code."""
        session_one = self.session(status.NOT_FOUND)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request('get', '/one')
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.NotFound)
                self.assertEqual(ex.status_code,
                                 status.NOT_FOUND)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_handle_bad_request(self, mock_Session):
        """Handles 400 Bad Request response code."""
        session_one = self.session(status.BAD_REQUEST)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request('get', '/one')
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.BadRequest)
                self.assertEqual(ex.status_code,
                                 status.BAD_REQUEST)

    @mock.patch(f'{service.__name__}.requests.Session')
    def test_handle_unexpected(self, mock_Session):
        """Handles unexpected response code."""
        session_one = self.session(status.USE_PROXY)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request('get', '/one')
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.RequestFailed)
                self.assertEqual(ex.status_code,
                                 status.USE_PROXY)

        session_one = self.session(status.OK)
        mock_Session.return_value = session_one
        self.app_one.config['BASE_ENDPOINT'] = 'https://fooservice/baz'
        service.HTTPIntegration.init_app(self.app_one)

        with self.app_one.app_context():
            try:
                service.HTTPIntegration.request(
                    'get',
                    '/one',
                    expected_code=[status.GONE]
                )
            except Exception as ex:
                self.assertIsInstance(ex, exceptions.RequestFailed)
                self.assertEqual(ex.status_code, status.OK)
