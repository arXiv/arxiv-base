import shutil
import tempfile
from copy import copy
from datetime import datetime, UTC

import pytest
import os

from flask import Flask
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, make_transient_to_detached

from .legacy import util
from .legacy.passwords import hash_password
from arxiv.base import Base
from ..base.middleware import wrap
from ..db import models
from ..db.models import configure_db_engine

from ..auth.auth import Auth
from ..auth.auth.middleware import AuthMiddleware


@pytest.fixture
def classic_db_engine():
    db_path = tempfile.mkdtemp()
    uri = f'sqlite:///{db_path}/test.db'
    engine = create_engine(uri)
    util.create_all(engine)
    yield engine
    shutil.rmtree(db_path)



@pytest.fixture
def classic_db_engine():
    db_path = tempfile.mkdtemp()
    uri = f'sqlite:///{db_path}/test.db'
    engine = create_engine(uri)
    util.create_all(engine)
    yield engine
    shutil.rmtree(db_path)


@pytest.fixture
def foouser(mocker):
    user_id = '15830'
    email = 'first@last.iv'
    # Why does this use a mock for the use and not a models.TapirUser?
    # Using an ORM obj caused problems when outside a session, but it seems
    # like there should be a way to do that.
    user = mocker.MagicMock(
        user_id=user_id,
        first_name='first',
        last_name='last',
        suffix_name='iv',
        email=email,
        policy_class=2,
        flag_edit_users=1,
        flag_email_verified=1,
        flag_edit_system=0,
        flag_approved=1,
        flag_deleted=0,
        flag_banned=0,
        tracking_cookie='foocookie',
    )
    nick = mocker.MagicMock(
        nickname='foouser',
        user_id=user_id,
        user_seq=1,
        flag_valid=1,
        role=0,
        policy=0,
        flag_primary=1
    )
    password = 'thepassword'
    hashed = hash_password(password)
    password = mocker.MagicMock(
        user_id=user_id,
        password_storage=2,
        password_enc=hashed,
        test_only_password=password,  # this is not on the real obj, just used so tests have access to it
    )
    n = util.epoch(datetime.now(tz=UTC))
    secret = 'foosecret'
    token = mocker.MagicMock(
        user_id=user_id,
        secret=secret,
        valid=1,
        issued_when=n,
        issued_to='127.0.0.1',
        remote_host='foohost.foo.com',
        session_id=0
    )
    user.tapir_nicknames = nick
    user.tapir_passwords = password
    user.tapir_tokens = token

    return user

@pytest.fixture
def db_with_user(classic_db_engine, foouser):
    # just combines classic_db_engine and foouser
    with Session(classic_db_engine, expire_on_commit=False) as session:
        user = models.TapirUser(
            user_id=foouser.user_id,
            first_name=foouser.first_name,
            last_name=foouser.last_name,
            suffix_name=foouser.suffix_name,
            email=foouser.email,
            policy_class=foouser.policy_class,
            flag_edit_users=foouser.flag_edit_users,
            flag_email_verified=foouser.flag_email_verified,
            flag_edit_system=foouser.flag_edit_system,
            flag_approved=foouser.flag_approved,
            flag_deleted=foouser.flag_deleted,
            flag_banned=foouser.flag_banned,
            tracking_cookie=foouser.tracking_cookie,
        )
        nick = models.TapirNickname(
            nickname=foouser.tapir_nicknames.nickname,
            user_id=foouser.tapir_nicknames.user_id,
            user_seq=foouser.tapir_nicknames.user_seq,
            flag_valid=foouser.tapir_nicknames.flag_valid,
            role=foouser.tapir_nicknames.role,
            policy=foouser.tapir_nicknames.policy,
            flag_primary=foouser.tapir_nicknames.flag_primary,
        )
        password = models.TapirUsersPassword(
            user_id=foouser.user_id,
            password_storage=foouser.tapir_passwords.password_storage,
            password_enc=foouser.tapir_passwords.password_enc,
        )
        token = models.TapirPermanentToken(
            user_id=foouser.user_id,
            secret=foouser.tapir_tokens.secret,
            valid=foouser.tapir_tokens.valid,
            issued_when=foouser.tapir_tokens.issued_when,
            issued_to=foouser.tapir_tokens.issued_to,
            remote_host=foouser.tapir_tokens.remote_host,
            session_id=foouser.tapir_tokens.session_id,
        )
        session.add(user)
        session.add(token)
        session.add(password)
        session.add(nick)
        session.commit()
        session.close()

    foouser.tapir_nicknames.nickname
    yield classic_db_engine

@pytest.fixture
def db_configed(db_with_user):
    configure_db_engine(db_with_user,None)


@pytest.fixture
def app(db_with_user):
    app = Flask('test_auth_app')

    engine, _ = configure_db_engine(db_with_user, None)
    Base(app)
    Auth(app)
    wrap(app, [AuthMiddleware])
    yield app


@pytest.fixture
def request_context(app):
    yield app.test_request_context()
