"""Testing helpers."""
import hashlib
import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime
from unittest import TestCase

from flask import Flask
from pytz import UTC
from sqlalchemy import select

from arxiv.config import Settings
from arxiv.db import transaction, models, Session
from arxiv.db.models import configure_db
from .. import util
from ..passwords import hash_password


@contextmanager
def temporary_db(db_uri: str, create: bool = True, drop: bool = True):
    """Provide an in-memory sqlite database for testing purposes."""
    app = Flask('foo')
    app.config['CLASSIC_SESSION_HASH'] = 'foohash'
    app.config['SESSION_DURATION'] = 3600
    app.config['CLASSIC_COOKIE_NAME'] = 'tapir_session'
    settings = Settings(
                        CLASSIC_DB_URI=db_uri,
                        LATEXML_DB_URI=None)

    engine, _ = configure_db (settings)

    with app.app_context():
        if create:
            util.create_all(engine)
        try:
            with transaction() as session:
                yield session
        finally:
            if drop:
                util.drop_all(engine)


class SetUpUserMixin(TestCase):
    """Mixin for creating a test user and other database goodies."""

    def setUp(self):
        """Set up the database."""
        self.db_path = tempfile.mkdtemp()
        self.db_uri = f'sqlite:///{self.db_path}/test.db'
        with open(self.db_path + '/test.txt', 'w') as f:
            f.write("test: " + os.environ.get("PYTEST_CURRENT_TEST"))

        self.user_id = '15830'
        self.app = Flask('test')

        self.app.config['CLASSIC_SESSION_HASH'] = 'foohash'
        self.app.config['CLASSIC_COOKIE_NAME'] = 'tapir_session_cookie'
        self.app.config['SESSION_DURATION'] = '36000'
        settings = Settings(
            CLASSIC_DB_URI=self.db_uri,
            LATEXML_DB_URI=None)

        self.engine, _ = models.configure_db(settings)

        with self.app.app_context():
                # Insert tapir policy classes

            util.create_all(self.engine)
            self.user_class = Session.scalar(
                select(models.TapirPolicyClass).where(models.TapirPolicyClass.class_id==2))
            self.email = 'first@last.iv'
            self.db_user = models.TapirUser(
                user_id=self.user_id,
                first_name='first',
                last_name='last',
                suffix_name='iv',
                email=self.email,
                policy_class=self.user_class.class_id,
                flag_edit_users=1,
                flag_email_verified=1,
                flag_edit_system=0,
                flag_approved=1,
                flag_deleted=0,
                flag_banned=0,
                tracking_cookie='foocookie',
            )
            self.username = 'foouser'
            self.db_nick = models.TapirNickname(
                nickname=self.username,
                user_id=self.user_id,
                user_seq=1,
                flag_valid=1,
                role=0,
                policy=0,
                flag_primary=1
            )
            self.password = 'thepassword'
            hashed = hash_password(self.password)
            self.db_password = models.TapirUsersPassword(
                user_id=self.user_id,
                password_storage=2,
                password_enc=hashed
            )
            n = util.epoch(datetime.now(tz=UTC))
            self.secret = 'foosecret'
            self.db_token = models.TapirPermanentToken(
                user_id=self.user_id,
                secret=self.secret,
                valid=1,
                issued_when=n,
                issued_to='127.0.0.1',
                remote_host='foohost.foo.com',
                session_id=0
            )
            Session.add(self.user_class)
            Session.add(self.db_user)
            Session.add(self.db_password)
            Session.add(self.db_nick)
            Session.add(self.db_token)
            Session.commit()

    def tearDown(self):
        """Drop tables from the in-memory db file."""
        util.drop_all(self.engine)
        shutil.rmtree(self.db_path)
