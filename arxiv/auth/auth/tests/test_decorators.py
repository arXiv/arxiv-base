"""Tests for :mod:`arxiv.users.auth.decorators`."""

import pytest
from datetime import datetime
from pytz import timezone, UTC

from flask import request, current_app
from werkzeug.exceptions import Unauthorized, Forbidden

from .. import scopes, decorators
from ... import domain

EASTERN = timezone('US/Eastern')
"""    @mock.patch(f'{decorators.__name__}.request')"""

def test_no_session(mocker, request_context):
    """No session is present on the request."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = None

        assert not hasattr(request, 'called')

        @decorators.scoped(scopes.CREATE_SUBMISSION)
        def _protected():
            request.called = True

        with pytest.raises(Unauthorized):
            _protected()

        assert not hasattr(request, 'called'),  "The protected function should not have its body called"


def test_scope_is_missing(mocker, request_context):
    """Session does not have required scope."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = domain.Session(
            session_id='fooid',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='235678',
                email='foo@foo.com',
                username='foouser'
            ),
            authorizations=domain.Authorizations(
                scopes=[scopes.VIEW_SUBMISSION]
            )
        )

        assert not hasattr(request, 'called')

        @decorators.scoped(scopes.CREATE_SUBMISSION)
        def protected():
            """A protected function."""
            request.called = True

        with pytest.raises(Forbidden):
            protected()

        assert not hasattr(request, 'called'),  "The protected function should not have its body called"

def test_scope_is_present(mocker, request_context):
     """Session has required scope."""
     with request_context:
         request.auth = domain.Session(
             session_id='fooid',
             start_time=datetime.now(tz=UTC),
             user=domain.User(
                 user_id='235678',
                 email='foo@foo.com',
                 username='foouser'
             ),
             authorizations=domain.Authorizations(
                 scopes=[scopes.VIEW_SUBMISSION, scopes.CREATE_SUBMISSION]
             )
         )

         assert not hasattr(request, 'called')

         @decorators.scoped(scopes.CREATE_SUBMISSION)
         def protected():
             """A protected function."""
             print("HERE IN PROTECTED")
             request.called = True

         protected()
         assert request.called


def test_user_and_client_are_missing(mocker, request_context):
    """Session does not user nor client information."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = domain.Session(
           session_id='fooid',
           start_time=datetime.now(tz=UTC),
           authorizations=domain.Authorizations(
               scopes=[scopes.CREATE_SUBMISSION]
           )
        )
        assert not hasattr(request, 'called')
        @decorators.scoped(scopes.CREATE_SUBMISSION)
        def protected():
            """A protected function."""
            request.called = True

        with pytest.raises(Unauthorized):
            protected()

        assert not hasattr(request, 'called'),  "The protected function should not have its body called"

def test_authorizer_returns_false(mocker, request_context):
    """Session has required scope, but authorizer func returns false."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = domain.Session(
            session_id='fooid',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='235678',
                email='foo@foo.com',
                username='foouser'
            ),
            authorizations=domain.Authorizations(
                scopes=[scopes.CREATE_SUBMISSION]
            )
        )
        assert not hasattr(request, 'called')
        assert not hasattr(request, 'authorizer_called')

        def return_false(session: domain.Session) -> bool:
            request.authorizer_called = True
            return False

        @decorators.scoped(scopes.CREATE_SUBMISSION, authorizer=return_false)
        def protected():
            """A protected function."""
            request.called = True

        with pytest.raises(Forbidden):
            protected()

        assert not hasattr(request, 'called')
        assert request.authorizer_called


def test_authorizer_returns_true(mocker, request_context):
    """Session has required scope, authorizer func returns true."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = domain.Session(
            session_id='fooid',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='235678',
                email='foo@foo.com',
                username='foouser'
            ),
            authorizations=domain.Authorizations(
                scopes=[scopes.CREATE_SUBMISSION]
            )
        )
        assert not hasattr(request, 'called')
        assert not hasattr(request, 'authorizer_called')

        def return_true(session: domain.Session) -> bool:
            request.authorizer_called = True
            return True

        @decorators.scoped(scopes.CREATE_SUBMISSION, authorizer=return_true)
        def protected():
            """A protected function."""
            request.called = True

        protected()

        assert request.called
        assert request.authorizer_called

def test_session_has_global(mocker, request_context):
    """Session has global scope, and authorizer func returns false."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = domain.Session(
            session_id='fooid',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='235678',
                email='foo@foo.com',
                username='foouser'
            ),
            authorizations=domain.Authorizations(
                scopes=[domain.Scope(scopes.CREATE_SUBMISSION).as_global()]
            )
        )

        def return_false(session: domain.Session) -> bool:
            return False

        @decorators.scoped(scopes.CREATE_SUBMISSION, authorizer=return_false)
        def protected():
            """A protected function."""
            request.called = True

        protected()
        assert request.called


def test_session_has_resource_scope(mocker, request_context):
    """Session has resource scope, and authorizer func returns false."""
    with request_context:
        mock_req = mocker.patch(f'{decorators.__name__}.request')
        mock_req.auth = domain.Session(
            session_id='fooid',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='235678',
                email='foo@foo.com',
                username='foouser'
            ),
            authorizations=domain.Authorizations(
                scopes=[domain.Scope(scopes.EDIT_SUBMISSION).for_resource('1')]
            )
        )

        def return_false(session: domain.Session) -> bool:
            return False

        def get_resource(*args, **kwargs) -> bool:
            return '1'

        @decorators.scoped(scopes.EDIT_SUBMISSION, resource=get_resource,
                           authorizer=return_false)
        def protected():
            """A protected function."""
            request.called = True

        protected()
        assert request.called
