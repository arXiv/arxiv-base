"""Integration tests for the session_store session store with Redis."""

from unittest import TestCase, mock
import jwt

from .... import domain
from .. import store


class TestDistributedSessionServiceIntegration(TestCase):
    """Test integration with Redis."""

    @classmethod
    def setUpClass(self):
        self.secret = 'bazsecret'

    @mock.patch(f'{store.__name__}.get_application_config')
    def test_store_create(self, mock_get_config):
        """An entry should be created in Redis."""
        mock_get_config.return_value = {
            'JWT_SECRET': self.secret,
            'REDIS_FAKE': True
        }
        ip = '127.0.0.1'
        remote_host = 'foo-host.foo.com'
        user = domain.User(
            user_id='1',
            username='theuser',
            email='the@user.com',
        )
        authorizations = domain.Authorizations(
            classic=2,
            scopes=['foo:write'],
            endorsements=[]
        )
        s = store.SessionStore.current_session()
        session = s.create(authorizations, ip, remote_host, user=user)
        cookie = s.generate_cookie(session)

        # API still works as expected.
        self.assertIsInstance(session, domain.Session)
        self.assertTrue(bool(session.session_id))
        self.assertIsNotNone(cookie)

        r = s.r
        raw = r.get(session.session_id)
        stored_data = jwt.decode(raw, self.secret, algorithms=['HS256'])
        cookie_data = jwt.decode(cookie, self.secret, algorithms=['HS256'])
        self.assertEqual(stored_data['nonce'], cookie_data['nonce'])

    # def test_invalidate_session(self):
    #     """Invalidate a session from the datastore."""
    #     r = rediscluster.StrictRedisCluster(startup_nodes=[dict(host='localhost', port='7000')])
    #     data_in = {'end_time': time.time() + 30 * 60, 'user_id': 1,
    #                'nonce': '123'}
    #     r.set('fookey', json.dumps(data_in))
    #     data0 = json.loads(r.get('fookey'))
    #     now = time.time()
    #     self.assertGreaterEqual(data0['end_time'], now)
    #     store.invalidate(
    #         store.current_session()._pack_cookie({
    #             'session_id': 'fookey',
    #             'nonce': '123',
    #             'user_id': 1
    #         })
    #     )
    #     data1 = json.loads(r.get('fookey'))
    #     now = time.time()
    #     self.assertGreaterEqual(now, data1['end_time'])

    @mock.patch(f'{store.__name__}.get_application_config')
    def test_delete_session(self, mock_get_config):
        """Delete a session from the datastore."""
        mock_get_config.return_value = {
            'JWT_SECRET': self.secret,
            'REDIS_FAKE': True
        }
        s = store.SessionStore.current_session()
        r = s.r
        r.set('fookey', b'foovalue')
        s.delete_by_id('fookey')
        self.assertIsNone(r.get('fookey'))
