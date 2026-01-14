"""User is attempting login with username+password."""

import pytest
from pytz import timezone

from .util import SetUpUserMixin
from .. import authenticate, exceptions

EASTERN = timezone("US/Eastern")


def test_no_username(app):
    """Username is not entered."""
    username = ""
    password = "foopass"
    with pytest.raises(exceptions.AuthenticationFailed):
        with app.app_context():
            authenticate.authenticate(username, password)


def test_no_password(app):
    """Password is not entered."""
    username = "foouser"
    password = ""
    with pytest.raises(exceptions.AuthenticationFailed):
        with app.app_context():
            authenticate.authenticate(username, password)


def test_password_is_incorrect(app):
    """Password is incorrect."""
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("foouser", "notthepassword")


def test_password_is_correct(app, foouser):
    """Password is correct."""
    with app.app_context():
        user, auths = authenticate.authenticate(
            foouser.tapir_nicknames.nickname, foouser.tapir_passwords.test_only_password
        )
        assert isinstance(user, authenticate.domain.User)
        assert isinstance(auths, authenticate.domain.Authorizations)
        assert user.user_id == foouser.user_id  # User ID is set correctly
        assert (
            user.username == foouser.tapir_nicknames.nickname
        )  # Username is set correctly
        assert user.email == foouser.email  # User email is set correctly
        assert auths.classic == 6  # Authorizations are set


def test_login_with_email_and_correct_password(app, foouser):
    """User attempts to log in with e-mail address."""
    with app.app_context():
        user, auths = authenticate.authenticate(
            foouser.email, foouser.tapir_passwords.test_only_password
        )
        assert isinstance(user, authenticate.domain.User)
        assert isinstance(auths, authenticate.domain.Authorizations)
        assert user.user_id == foouser.user_id  # User ID is set correctly
        assert (
            user.username == foouser.tapir_nicknames.nickname
        )  # Username is set correctly
        assert user.email == foouser.email  # User email is set correctly
        assert auths.classic == 6  # authorizations are set


def test_no_such_user(app):
    """Username does not exist."""
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("nobody", "thepassword")


def test_bad_data(app):
    """Test with bad data."""
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("abc", "")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("abc", 234)
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("abc", "β")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("", "password")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("β", "password")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate("long" * 100, "password")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(1234, "password")

        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, "abcc-something")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, "-something")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, ("long" * 20) + "-something")
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, "1234-" + 40 * "long")
