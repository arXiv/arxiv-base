"""Tests for :mod:`arxiv.users.auth.sessions.store`."""

from unittest import TestCase, mock
import time
import jwt
import json
from datetime import datetime, timedelta
from pytz import timezone, UTC
from redis.exceptions import ConnectionError

from .... import domain
from .. import store

EASTERN = timezone('US/Eastern')


class TestDistributedSessionService(TestCase):
    """The store session service puts sessions in a key-value store."""

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster')
    def test_create(self, mock_redis, mock_get_config):
        """Accept a :class:`.User` and returns a :class:`.Session`."""
        mock_get_config.return_value = {'JWT_SECRET': 'foosecret'}
        mock_redis.exceptions.ConnectionError = ConnectionError
        mock_redis_connection = mock.MagicMock()
        mock_redis.StrictRedisCluster.return_value = mock_redis_connection
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
        r = store.SessionStore('localhost', 7000, 0, 'foosecret')
        session = r.create(auths, ip, remote_host, user=user)
        cookie = r.generate_cookie(session)
        self.assertIsInstance(session, domain.Session)
        self.assertTrue(bool(session.session_id))
        self.assertIsNotNone(cookie)
        self.assertEqual(mock_redis_connection.set.call_count, 1)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster')
    def test_delete(self, mock_redis, mock_get_config):
        """Delete a session from the datastore."""
        mock_get_config.return_value = {'JWT_SECRET': 'foosecret'}
        mock_redis.exceptions.ConnectionError = ConnectionError
        mock_redis_connection = mock.MagicMock()
        mock_redis.StrictRedisCluster.return_value = mock_redis_connection
        r = store.SessionStore('localhost', 7000, 0, 'foosecret')
        r.delete_by_id('fookey')
        self.assertEqual(mock_redis_connection.delete.call_count, 1)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster')
    def test_connection_failed(self, mock_redis, mock_get_config):
        """:class:`.SessionCreationFailed` is raised when creation fails."""
        mock_get_config.return_value = {'JWT_SECRET': 'foosecret'}
        mock_redis.exceptions.ConnectionError = ConnectionError
        mock_redis_connection = mock.MagicMock()
        mock_redis_connection.set.side_effect = ConnectionError
        mock_redis.StrictRedisCluster.return_value = mock_redis_connection
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
        r = store.SessionStore('localhost', 7000, 0, 'foosecret')
        with self.assertRaises(store.SessionCreationFailed):
            r.create(auths, ip, remote_host, user=user)


class TestGetSession(TestCase):
    """Tests for :func:`store.SessionStore.current_session().load`."""

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_not_a_token(self, mock_get_redis, mock_get_config):
        """Something other than a JWT is passed."""
        mock_get_config.return_value = {
            'JWT_SECRET': 'barsecret',
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_get_redis.return_value = mock_redis
        with self.assertRaises(store.InvalidToken):
            store.SessionStore.current_session().load('notatoken')

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_malformed_token(self, mock_get_redis, mock_get_config):
        """A JWT with missing claims is passed."""
        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_get_redis.return_value = mock_redis
        required_claims = ['session_id', 'nonce']
        for exc in required_claims:
            claims = {claim: '' for claim in required_claims if claim != exc}
            malformed_token = jwt.encode(claims, secret)
            with self.assertRaises(store.InvalidToken):
                store.SessionStore.current_session().load(malformed_token)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_token_with_bad_encryption(self, mock_get_redis, mock_get_config):
        """A JWT produced with a different secret is passed."""
        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_get_redis.return_value = mock_redis
        start_time = datetime.now(tz=UTC)
        end_time = start_time + timedelta(seconds=7200)
        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': end_time.isoformat()
        }
        bad_token = jwt.encode(claims, 'nottherightsecret')
        with self.assertRaises(store.InvalidToken):
            store.SessionStore.current_session().load(bad_token)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_expired_token(self, mock_get_redis, mock_get_config):
        """A JWT produced with a different secret is passed."""
        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        start_time = datetime.now(tz=UTC)
        mock_redis.get.return_value = json.dumps({
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': start_time.isoformat(),
        })
        mock_get_redis.return_value = mock_redis

        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': start_time.isoformat(),
        }
        expired_token = jwt.encode(claims, secret)
        with self.assertRaises(store.InvalidToken):
            store.SessionStore.current_session().load(expired_token)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_forged_token(self, mock_get_redis, mock_get_config):
        """A JWT with the wrong nonce is passed."""
        start_time = datetime.now(tz=UTC)
        end_time = start_time + timedelta(seconds=7200)

        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_redis.get.return_value = jwt.encode({
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290098',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'user': {
                'user_id': '1235',
                'username': 'foouser',
                'email': 'foo@foo.com'
            }
        }, secret)
        mock_get_redis.return_value = mock_redis

        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',    # <- Doesn't match!
            'expires': end_time.isoformat(),
        }
        expired_token = jwt.encode(claims, secret)
        with self.assertRaises(store.InvalidToken):
            # loaded token is getting non Datetime end_time
            store.SessionStore.current_session().load(expired_token)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_other_forged_token(self, mock_get_redis, mock_get_config):
        """A JWT with the wrong user_id is passed."""
        start_time = datetime.now(tz=UTC)
        end_time = start_time + timedelta(seconds=7200)

        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_redis.get.return_value = jwt.encode({
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'start_time': start_time.isoformat(),
            'user': {
                'user_id': '1235',
                'username': 'foouser',
                'email': 'foo@foo.com'
            }
        }, secret)
        mock_get_redis.return_value = mock_redis
        claims = {
            'user_id': '1234',  # <- Doesn't match!
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': end_time.isoformat(),
        }
        expired_token = jwt.encode(claims, secret)
        with self.assertRaises(store.InvalidToken):
            store.SessionStore.current_session().load(expired_token)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_empty_session(self, mock_get_redis, mock_get_config):
        """Session has been removed, or may never have existed."""
        start_time = datetime.now(tz=UTC)
        end_time = start_time + timedelta(seconds=7200)

        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_redis.get.return_value = ''    # <- Empty record!
        mock_get_redis.return_value = mock_redis

        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290099',
            'expires': end_time.isoformat(),
        }
        expired_token = jwt.encode(claims, secret)
        with self.assertRaises(store.UnknownSession):
            store.SessionStore.current_session().load(expired_token)

    @mock.patch(f'{store.__name__}.get_application_config')
    @mock.patch(f'{store.__name__}.rediscluster.StrictRedisCluster')
    def test_valid_token(self, mock_get_redis, mock_get_config):
        """A valid token is passed."""
        start_time = datetime.now(tz=UTC)
        end_time = start_time + timedelta(seconds=7200)

        secret = 'barsecret'
        mock_get_config.return_value = {
            'JWT_SECRET': secret,
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '1234',
            'REDIS_DATABASE': 4
        }
        mock_redis = mock.MagicMock()
        mock_redis.get.return_value = jwt.encode({
            'session_id': 'ajx9043jjx00s',
            'start_time': datetime.now(tz=UTC).isoformat(),
            'nonce': '0039299290098',
            'user': {
                'user_id': '1234',
                'username': 'foouser',
                'email': 'foo@foo.com'
            }
        }, secret)
        mock_get_redis.return_value = mock_redis

        claims = {
            'user_id': '1234',
            'session_id': 'ajx9043jjx00s',
            'nonce': '0039299290098',
            'expires': end_time.isoformat(),
        }
        valid_token = jwt.encode(claims, secret)

        session = store.SessionStore.current_session().load(valid_token)
        self.assertIsInstance(session, domain.Session, "Returns a session")
