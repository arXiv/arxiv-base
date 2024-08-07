"""Tests for :mod:`accounts.services.user_data`."""

from unittest import TestCase, mock
from datetime import datetime
from pytz import timezone, UTC
import tempfile
import shutil
import hashlib

from flask import Flask

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from arxiv.config import Settings
from arxiv.db import models

from .. import authenticate, exceptions, util

from .util import SetUpUserMixin

from ..passwords import hash_password

EASTERN = timezone('US/Eastern')


class TestAuthenticateWithPermanentToken(SetUpUserMixin):
    """User has a permanent token."""

    #def setUp(self):
    #     """Instantiate a user and its credentials in the DB."""
    #     self.db = f'sqlite:///:memory:'
    #     self.user_id = '1'
    #
    #     self.app = Flask('test')
    #     settings = Settings(
    #                     CLASSIC_DB_URI=self.db,
    #                     LATEXML_DB_URI=None)
    #
    #     self.engine, _ = models.configure_db(settings)
    #
    #     with temporary_db(self.db, drop=False) as session:
    #         self.user_class = session.scalar(
    #             select(models.TapirPolicyClass).where(models.TapirPolicyClass.class_id==2))
    #         self.email = 'first@last.iv'
    #         self.db_user = models.TapirUser(
    #             user_id=self.user_id,
    #             first_name='first',
    #             last_name='last',
    #             suffix_name='iv',
    #             email=self.email,
    #             policy_class=self.user_class.class_id,
    #             flag_edit_users=1,
    #             flag_email_verified=1,
    #             flag_edit_system=0,
    #             flag_approved=1,
    #             flag_deleted=0,
    #             flag_banned=0,
    #             tracking_cookie='foocookie',
    #         )
    #         self.username = 'foouser'
    #         self.db_nick = models.TapirNickname(
    #             nickname=self.username,
    #             user_id=self.user_id,
    #             user_seq=1,
    #             flag_valid=1,
    #             role=0,
    #             policy=0,
    #             flag_primary=1
    #         )
    #         self.salt = b'foo'
    #         self.password = b'thepassword'
    #         hashed = hashlib.sha1(self.salt + b'-' + self.password).digest()
    #         self.db_password = models.TapirUsersPassword(
    #             user_id=self.user_id,
    #             password_storage=2,
    #             password_enc=hashed
    #         )
    #         n = util.epoch(datetime.now(tz=UTC))
    #         self.secret = 'foosecret'
    #         self.db_token = models.TapirPermanentToken(
    #             user_id=self.user_id,
    #             secret=self.secret,
    #             valid=1,
    #             issued_when=n,
    #             issued_to='127.0.0.1',
    #             remote_host='foohost.foo.com',
    #             session_id=0
    #         )
    #         session.add(self.user_class)
    #         session.add(self.db_user)
    #         session.add(self.db_password)
    #         session.add(self.db_nick)
    #         session.add(self.db_token)
    #         session.commit()
    #
    # def tearDown(self):
    #     """Drop tables from the in-memory db file."""
    #     util.drop_all(self.engine)

    def test_token_is_malformed(self):
        """Token is present, but it has the wrong format."""
        bad_token = 'footokenhasnohyphen'
        with self.app.app_context():
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(token=bad_token)

    def test_token_is_incorrect(self):
        """Token is present, but there is no such token in the database."""
        bad_token = '1234-nosuchtoken'
        # with temporary_db(self.db, create=False):
        with self.app.app_context():
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(token=bad_token)

    def test_token_is_invalid(self):
        """The token is present, but it is not valid."""
        with self.app.app_context():
            authenticate._invalidate_token(self.user_id, self.secret)

            with self.assertRaises(exceptions.AuthenticationFailed):
                token = f'{self.user_id}-{self.secret}'
                authenticate.authenticate(token=token)

    def test_token_is_valid(self):
        """The token is valid!."""
        with self.app.app_context():
            token = f'{self.user_id}-{self.secret}'
            user, auths = authenticate.authenticate(token=token)
            self.assertIsInstance(user, authenticate.domain.User,
                                  "Returns data about the user")
            self.assertIsInstance(auths, authenticate.domain.Authorizations,
                                  "Returns authorization data")
            self.assertEqual(user.user_id, self.user_id,
                             "User ID is set correctly")
            self.assertEqual(user.username, self.username,
                             "Username is set correctly")
            self.assertEqual(user.email, self.email,
                             "User email is set correctly")
            self.assertEqual(auths.classic, 6,
                             "authorizations are set")


class TestAuthenticateWithPassword(SetUpUserMixin):
    """User is attempting login with username+password."""

    def test_no_username(self):
        """Username is not entered."""
        username = ''
        password = 'foopass'
        with self.assertRaises(exceptions.AuthenticationFailed):
            with self.app.app_context():
                authenticate.authenticate(username, password)

    def test_no_password(self):
        """Password is not entered."""
        username = 'foouser'
        password = ''
        with self.assertRaises(exceptions.AuthenticationFailed):
            with self.app.app_context():
                authenticate.authenticate(username, password)

    def test_password_is_incorrect(self):
        """Password is incorrect."""
        with self.app.app_context():
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('foouser', 'notthepassword')

    def test_password_is_correct(self):
        """Password is correct."""
        with self.app.app_context():

            user, auths = authenticate.authenticate('foouser', 'thepassword')
            self.assertIsInstance(user, authenticate.domain.User,
                                  "Returns data about the user")
            self.assertIsInstance(auths, authenticate.domain.Authorizations,
                                  "Returns authorization data")
            self.assertEqual(user.user_id, self.user_id,
                             "User ID is set correctly")
            self.assertEqual(user.username, self.username,
                             "Username is set correctly")
            self.assertEqual(user.email, self.email,
                             "User email is set correctly")
            self.assertEqual(auths.classic, 6,
                             "Authorizations are set")

    def test_login_with_email_and_correct_password(self):
        """User attempts to log in with e-mail address."""
        with self.app.app_context():
            user, auths = authenticate.authenticate('first@last.iv',
                                                    'thepassword')
            self.assertIsInstance(user, authenticate.domain.User,
                                  "Returns data about the user")
            self.assertIsInstance(auths, authenticate.domain.Authorizations,
                                  "Returns authorization data")
            self.assertEqual(user.user_id, self.user_id,
                             "User ID is set correctly")
            self.assertEqual(user.username, self.username,
                             "Username is set correctly")
            self.assertEqual(user.email, self.email,
                             "User email is set correctly")
            self.assertEqual(auths.classic, 6,
                             "authorizations are set")

    def test_no_such_user(self):
        """Username does not exist."""
        with self.app.app_context():
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('nobody', 'thepassword')


    def test_bad_data(self):
        """Test with bad data."""
        with self.app.app_context():
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('abc', '')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('abc', 234)
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('abc', 'β')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('', 'password')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('β', 'password')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate('long'*100, 'password')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(1234, 'password')


            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(None, None, 'abcc-something')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(None, None, '-something')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(None, None, ('long'*20) + '-something')
            with self.assertRaises(exceptions.AuthenticationFailed):
                authenticate.authenticate(None, None, '1234-' + 40 * 'long')
