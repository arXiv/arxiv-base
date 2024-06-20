"""Tests for legacy_users service."""
import time
from typing import Optional
from unittest import mock, TestCase
from datetime import datetime
from pytz import timezone, UTC

from flask import Flask

from arxiv.db import models, session
from .. import exceptions, sessions, util, cookies

from .util import temporary_db

EASTERN = timezone('US/Eastern')


class TestCreateSession(TestCase):
    """Tests for public function :func:`.`."""

    @mock.patch(f'{sessions.__name__}.util.get_session_duration')
    def test_create(self, mock_get_session_duration):
        """Accept a :class:`.User` and returns a :class:`.Session`."""
        mock_get_session_duration.return_value = 36000
        user = sessions.domain.User(
            user_id="1",
            username='theuser',
            email='the@user.com',
        )
        auths = sessions.domain.Authorizations(classic=6)
        ip_address = '127.0.0.1'
        remote_host = 'foo-host.foo.com'
        tracking = "1.foo"
        with temporary_db('sqlite:///:memory:', create=True):
            user_session = sessions.create(auths, ip_address, remote_host,
                                        tracking, user=user)
            self.assertIsInstance(user_session, sessions.domain.Session)
            tapir_session = sessions._load(user_session.session_id)
            self.assertIsNotNone(user_session, 'verifying we have a session')
            if tapir_session is not None:
                self.assertEqual(
                    tapir_session.session_id,
                    int(user_session.session_id),
                    "Returned session has correct session id."
                )
                self.assertEqual(tapir_session.user_id, int(user.user_id),
                                "Returned session has correct user id.")
                self.assertEqual(tapir_session.end_time, 0,
                                "End time is 0 (no end time)")

            tapir_session_audit = sessions._load_audit(user_session.session_id)
            self.assertIsNotNone(tapir_session_audit)
            if tapir_session_audit is not None:
                self.assertEqual(
                    tapir_session_audit.session_id,
                    int(user_session.session_id),
                    "Returned session audit has correct session id."
                )
                self.assertEqual(
                    tapir_session_audit.ip_addr,
                    user_session.ip_address,
                    "Returned session audit has correct ip address"
                )
                self.assertEqual(
                    tapir_session_audit.remote_host,
                    user_session.remote_host,
                    "Returned session audit has correct remote host"
                )


class TestInvalidateSession(TestCase):
    """Tests for public function :func:`.invalidate`."""

    @mock.patch(f'{cookies.__name__}.util.get_session_duration')
    def test_invalidate(self, mock_get_duration):
        """The session is invalidated by setting `end_time`."""
        mock_get_duration.return_value = 36000
        session_id = "424242424"
        user_id = "12345"
        ip = "127.0.0.1"
        capabilities = 6
        start = datetime.now(tz=UTC)

        with temporary_db('sqlite:///:memory:') as db_session:
            cookie = cookies.pack(session_id, user_id, ip, start, capabilities)
            with util.transaction() as db_session:
                tapir_session = models.TapirSession(
                    session_id=session_id,
                    user_id=12345,
                    last_reissue=util.epoch(start),
                    start_time=util.epoch(start),
                    end_time=0
                )
                db_session.add(tapir_session)

            sessions.invalidate(cookie)
            tapir_session = sessions._load(session_id)
            time.sleep(1)
            self.assertGreaterEqual(util.now(), tapir_session.end_time)

    @mock.patch(f'{cookies.__name__}.util.get_session_duration')
    def test_invalidate_nonexistant_session(self, mock_get_duration):
        """An exception is raised if the session doesn't exist."""
        mock_get_duration.return_value = 36000
        with temporary_db('sqlite:///:memory:'):
            with self.assertRaises(exceptions.UnknownSession):
                sessions.invalidate('1:1:10.10.10.10:1531145500:4')
