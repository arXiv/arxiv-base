"""Tests for :class:`arxiv.users.auth.Auth`."""

import shutil
import tempfile
from logging import DEBUG
import pytest

from datetime import datetime

from flask import Flask
from pytz import timezone, UTC

from arxiv.base import Base
from arxiv.base.middleware import wrap
from arxiv.config import Settings
from arxiv.db import configure_db
from .. import Auth
from ..middleware import AuthMiddleware
from ... import auth, domain

EASTERN = timezone("US/Eastern")


@pytest.fixture()
def app_ext():
    db_path = tempfile.mkdtemp()
    app = Flask("test_auth_app")
    app.config["CLASSIC_DATABASE_URI"] = f"sqlite:///{db_path}/test.db"
    app.config["CLASSIC_SESSION_HASH"] = f"fake set in {__file__}"
    app.config["SESSION_DURATION"] = f"fake set in {__file__}"
    app.config["CLASSIC_COOKIE_NAME"] = f"fake set in {__file__}"
    app.config["AUTH_UPDATED_SESSION_REF"] = True
    settings = Settings(
        CLASSIC_DB_URI=app.config["CLASSIC_DATABASE_URI"], LATEXML_DB_URI=None
    )
    engine, _ = configure_db(settings)
    app.config["DB_ENGINE"] = engine

    Base(app)

    Auth(app)
    wrap(app, [AuthMiddleware])
    yield app

    shutil.rmtree(db_path)


@pytest.fixture
def app_with_cookie(app_ext):
    app_ext.config["CLASSIC_COOKIE_NAME"] = "foo_cookie"
    app_ext.config["CLASSIC_SESSION_HASH"] = "1234"
    app_ext.config["SESSION_DURATION"] = "3600"
    return app_ext


def test_no_session_legacy_available(mocker, app_with_cookie):
    """No session is present on the request, but database is present."""
    inst = app_with_cookie.config["arxiv_auth.Auth"]
    auth.logger.setLevel(DEBUG)
    with app_with_cookie.test_request_context():
        mock_legacy = mocker.patch(f"{auth.__name__}.legacy")
        mock_request = mocker.patch(f"{auth.__name__}.request")
        mock_request.environ = {
            "auth": None,
            "HTTP_COOKIE": "foo_cookie=sessioncookie123",
        }

        mock_legacy.util.is_configured.return_value = True
        mock_legacy.sessions.load.return_value = None

        inst.load_session()
        assert mock_request.auth is None

        assert mock_legacy.sessions.load.call_count == 1, (
            "An attempt is made to load a legacy session"
        )


def test_legacy_is_valid(mocker, app_with_cookie):
    """A valid legacy session is available."""
    inst = app_with_cookie.config["arxiv_auth.Auth"]
    with app_with_cookie.test_request_context():
        mock_legacy = mocker.patch(f"{auth.__name__}.legacy")
        mock_request = mocker.patch(f"{auth.__name__}.request")
        mock_request.environ = {
            "auth": None,
            "HTTP_COOKIE": "foo_cookie=sessioncookie123",
        }

        mock_request.auth = None
        mock_legacy.is_configured.return_value = True
        session = domain.Session(
            session_id="fooid",
            start_time=datetime.now(tz=UTC),
            user=domain.User(user_id="235678", email="foo@foo.com", username="foouser"),
            authorizations=domain.Authorizations(scopes=[auth.scopes.VIEW_SUBMISSION]),
        )
        mock_legacy.sessions.load.return_value = session

        inst.load_session()
        assert mock_request.auth == session, (
            "Session is attached to the request at auth"
        )


def test_auth_session_rename(mocker, app_with_cookie):
    """
    The auth session is accessed via ``request.auth``.

    Per ARXIVNG-1920 using ``request.auth`` is deprecated.
    """
    inst = app_with_cookie.config["arxiv_auth.Auth"]
    with app_with_cookie.test_request_context():
        mock_legacy = mocker.patch(f"{auth.__name__}.legacy")
        mock_request = mocker.patch(f"{auth.__name__}.request")
        mock_request.environ = {
            "auth": None,
            "HTTP_COOKIE": "foo_cookie=sessioncookie123",
        }

        mock_request.auth = None
        mock_legacy.is_configured.return_value = True

        authex = domain.Session(
            session_id="fooid",
            start_time=datetime.now(tz=UTC),
            user=domain.User(user_id="235678", email="foo@foo.com", username="foouser"),
            authorizations=domain.Authorizations(scopes=[auth.scopes.VIEW_SUBMISSION]),
        )
        mock_legacy.sessions.load.return_value = authex

        inst.load_session()
        assert mock_request.auth == authex, "Auth is attached to the request"


def test_middleware_exception(mocker, app_with_cookie):
    """Middleware has passed an exception."""
    inst = app_with_cookie.config["arxiv_auth.Auth"]
    with app_with_cookie.test_request_context():
        mock_request = mocker.patch(f"{auth.__name__}.request")
        mock_request.environ = {"auth": RuntimeError("Nope!")}

        with pytest.raises(RuntimeError):
            inst.load_session()
