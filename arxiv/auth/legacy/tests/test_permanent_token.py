"""Tests for :mod:`accounts.services.user_data`."""
import pytest
from pytz import timezone

from .util import SetUpUserMixin
from .. import authenticate, exceptions

EASTERN = timezone('US/Eastern')

def test_permanent_token_bad(app, foouser):
    with app.app_context():
        bad_token = 'footokenhasnohyphen'
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(token=bad_token) #  Token is present, but it has the wrong format.

        bad_token = '1234-nosuchtoken'
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(token=bad_token) # Token is present, but there is no such token in the database.
            
        authenticate._invalidate_token(foouser.user_id, foouser.tapir_tokens.secret)
        with pytest.raises(exceptions.AuthenticationFailed):
                token = f'{foouser.user_id}-{foouser.tapir_tokens.secret}'
                authenticate.authenticate(token=token) # The token is present, but it is not valid.

def test_permanent_token(app, foouser):
    """The token is valid."""
    with app.app_context():
        token = f'{foouser.user_id}-{foouser.tapir_tokens.secret}'
        user, auths = authenticate.authenticate(token=token)
        isinstance(user, authenticate.domain.User)
        isinstance(auths, authenticate.domain.Authorizations)
        assert user.user_id == foouser.user_id
        assert user.username == foouser.tapir_nicknames.nickname
        assert user.email == foouser.email
        assert auths.classic == 6
