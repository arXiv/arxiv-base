"""Tests for :mod:`arxiv.auth.auth.sessions.store`.

Sessions are stateless self-contained JWT cookies; there is no Redis store, so
these tests exercise cookie packing/unpacking and stateless ``load`` only.
"""

from unittest import TestCase, mock
import jwt
from datetime import datetime, timedelta
from pytz import timezone, UTC

from .... import domain
from .. import store

EASTERN = timezone('US/Eastern')


class TestStatelessSessionService(TestCase):
    """The store mints and reads self-contained JWT session cookies."""

    def test_create(self):
        """Accept a :class:`.User` and return a :class:`.Session`."""
        ip = '127.0.0.1'
        remote_host = 'foo-host.foo.com'
        user = domain.User(
            user_id='1',
            username='theuser',
            email='the@user.com'
        )
        auths = domain.Authorizations(
            classic=2,
            scopes=['foo:write'],
            endorsements=[]
        )
        r = store.SessionStore('', 0, 0, 'foosecret')
        session = r.create(auths, ip, remote_host, user=user)
        cookie = r.generate_cookie(session)
        self.assertIsInstance(session, domain.Session)
        self.assertTrue(bool(session.session_id))
        self.assertIsNotNone(cookie)

    def test_generate_cookie_claims(self):
        """The cookie is a signed JWT carrying the session claims."""
        secret = 'foosecret'
        user = domain.User(user_id='42', username='u', email='u@x.com')
        auths = domain.Authorizations(classic=2, scopes=[], endorsements=[])
        r = store.SessionStore('', 0, 0, secret)
        session = r.create(auths, '127.0.0.1', 'host', user=user)
        cookie = r.generate_cookie(session)
        claims = jwt.decode(cookie, secret, algorithms=['HS256'])
        self.assertEqual(claims['user_id'], '42')
        self.assertEqual(claims['session_id'], session.session_id)
        self.assertEqual(claims['nonce'], session.nonce)
        self.assertIn('expires', claims)

    def test_pack_cookie_requires_nonce(self):
        """:func:`pack_cookie` refuses a session without a nonce."""
        user = domain.User(user_id='42', username='u', email='u@x.com')
        end_time = datetime.now(tz=UTC) + timedelta(seconds=7200)
        session = domain.Session(
            session_id='s1', user=user,
            start_time=datetime.now(tz=UTC), end_time=end_time, nonce=None)
        with self.assertRaises(RuntimeError):
            store.pack_cookie(session, 'foosecret')

    def test_delete_is_noop(self):
        """Deleting a stateless session is a harmless no-op."""
        r = store.SessionStore('', 0, 0, 'foosecret')
        self.assertIsNone(r.delete_by_id('fookey'))
        self.assertIsNone(r.delete('anycookie'))

    def test_load_by_id_unsupported(self):
        """A stateless session cannot be loaded by ID alone."""
        r = store.SessionStore('', 0, 0, 'foosecret')
        with self.assertRaises(store.UnknownSession):
            r.load_by_id('somesession')

    def test_generate_nonce(self):
        """:func:`_generate_nonce` produces a numeric string."""
        nonce = store._generate_nonce()
        self.assertEqual(len(nonce), 8)
        self.assertTrue(nonce.isdigit())


class TestLoad(TestCase):
    """Tests for stateless :meth:`store.SessionStore.load`."""

    def setUp(self):
        self.secret = 'barsecret'
        self.store = store.SessionStore('', 0, 0, self.secret)

    def test_not_a_token(self):
        """Something other than a JWT is passed."""
        with self.assertRaises(store.InvalidToken):
            self.store.load('notatoken')

    def test_malformed_token(self):
        """A JWT missing a required claim is passed."""
        end_time = datetime.now(tz=UTC) + timedelta(seconds=7200)
        required_claims = ['user_id', 'session_id', 'nonce', 'expires']
        full = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': end_time.isoformat(),
        }
        for missing in required_claims:
            claims = {k: v for k, v in full.items() if k != missing}
            malformed_token = jwt.encode(claims, self.secret)
            with self.assertRaises(store.InvalidToken):
                self.store.load(malformed_token)

    def test_token_with_bad_encryption(self):
        """A JWT produced with a different secret is passed."""
        end_time = datetime.now(tz=UTC) + timedelta(seconds=7200)
        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': end_time.isoformat()
        }
        bad_token = jwt.encode(claims, 'nottherightsecret')
        with self.assertRaises(store.InvalidToken):
            self.store.load(bad_token)

    def test_expired_token(self):
        """A cookie whose expiry is in the past is rejected."""
        past = datetime.now(tz=UTC) - timedelta(seconds=1)
        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': past.isoformat(),
        }
        expired_token = jwt.encode(claims, self.secret)
        with self.assertRaises(store.ExpiredToken):
            self.store.load(expired_token)

    def test_valid_token(self):
        """A valid token reconstructs a :class:`.Session` from its claims."""
        end_time = datetime.now(tz=UTC) + timedelta(seconds=7200)
        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290098',
            'expires': end_time.isoformat(),
        }
        valid_token = jwt.encode(claims, self.secret)
        session = self.store.load(valid_token)
        self.assertIsInstance(session, domain.Session, "Returns a session")
        self.assertEqual(session.session_id, 'ajx9043jjx00s')
        self.assertEqual(session.user.user_id, '1234')

    def test_load_no_decode_returns_cookie(self):
        """``decode=False`` returns the cookie unchanged."""
        end_time = datetime.now(tz=UTC) + timedelta(seconds=7200)
        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290098',
            'expires': end_time.isoformat(),
        }
        valid_token = jwt.encode(claims, self.secret)
        self.assertEqual(self.store.load(valid_token, decode=False),
                         valid_token)
