"""Tests for :mod:`accounts.services.user_data`."""
import shutil
import tempfile

import pytest
from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from arxiv.db import Session as arXiv_session
from arxiv.db.models import configure_db_engine

from .util import SetUpUserMixin
from .. import authenticate, exceptions, util

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


@pytest.fixture
def session_elsewhere(db_with_user):
    """A session that sees foouser, while arxiv.db's default Session sees an empty database."""
    db_path = tempfile.mkdtemp()
    empty = create_engine(f'sqlite:///{db_path}/empty.db')
    util.create_arxiv_db_schema(empty)
    configure_db_engine(empty, None)
    arXiv_session.remove()
    with Session(db_with_user) as session:
        yield session
    arXiv_session.remove()
    empty.dispose()
    shutil.rmtree(db_path)


def test_permanent_token_uses_the_callers_session(foouser, session_elsewhere):
    """The token and its user are both looked up in the session passed in."""
    token = f'{foouser.user_id}-{foouser.tapir_tokens.secret}'
    user, _ = authenticate.authenticate(token=token, session=session_elsewhere)
    assert user.user_id == foouser.user_id


def test_invalidate_token_uses_the_callers_session(foouser, session_elsewhere):
    authenticate._invalidate_token(foouser.user_id, foouser.tapir_tokens.secret, session=session_elsewhere)
    with pytest.raises(exceptions.AuthenticationFailed):
        token = f'{foouser.user_id}-{foouser.tapir_tokens.secret}'
        authenticate.authenticate(token=token, session=session_elsewhere)
