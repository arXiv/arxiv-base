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
