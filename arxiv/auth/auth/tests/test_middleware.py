"""Test :mod:`arxiv.users.auth.middleware`."""

import os
from unittest import TestCase, mock
from datetime import datetime
from pytz import timezone, UTC
import json

from flask import Flask, Blueprint
from flask import request, current_app

from arxiv.base.middleware import wrap
from arxiv import status

from ..middleware import AuthMiddleware
from .. import tokens, scopes
from ... import domain

EASTERN = timezone('US/Eastern')


blueprint = Blueprint('fooprint', __name__, url_prefix='')


@blueprint.route('/public', methods=['GET'])
def public():     # type: ignore
    """Return the request auth as a JSON document, or raise exceptions."""
    data = request.environ.get('auth')
    if data:
        if isinstance(data, Exception):
            raise data
        return domain.Session.parse_obj(data).json_safe_dict()
    return json.dumps({})


class TestAuthMiddleware(TestCase):
    """Test :class:`.AuthMiddleware` on a Flask app."""

    def setUp(self):
        """Instantiate an app and attach middlware."""
        self.secret = 'foosecret'
        self.app = Flask('foo')
        os.environ['JWT_SECRET'] = self.secret
        self.app.register_blueprint(blueprint)
        wrap(self.app, [AuthMiddleware])
        self.client = self.app.test_client()

    def test_no_token(self):
        """No token is passed in the request."""
        response = self.client.get('/public')
        data = json.loads(response.data)
        self.assertEqual(data, {}, "No session data is set")

    def test_user_token(self):
        """A valid user token is passed in the request."""
        session = domain.Session(
            session_id='foo1234',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='43219',
                email='foo@foo.com',
                username='foouser',
                name=domain.UserFullName(forename='Foo', surname='User')
            ),
            # client: Optional[Client] = None
            # end_time: Optional[datetime] = None
            authorizations=domain.Authorizations(
                scopes=scopes.GENERAL_USER
            ),
            ip_address='10.10.10.10',
            remote_host='foo-host.something.com',
            nonce='asdfkjl3kmalkml;xml;mla'
        )
        token = tokens.encode(session, self.secret)
        response = self.client.get('/public', headers={'Authorization': token})
        data = json.loads(response.data)
        self.assertEqual(data, session.json_safe_dict(),
                         "Session data are added to the request")

    def test_forged_user_token(self):
        """A forged user token is passed in the request."""
        session = domain.Session(
            session_id='foo1234',
            start_time=datetime.now(tz=UTC),
            user=domain.User(
                user_id='43219',
                email='foo@foo.com',
                username='foouser',
                name=domain.UserFullName(forename='Foo', surname='User')
            ),
            # client: Optional[Client] = None
            # end_time: Optional[datetime] = None
            authorizations=domain.Authorizations(
                scopes=scopes.GENERAL_USER
            ),
            ip_address='10.10.10.10',
            remote_host='foo-host.something.com',
            nonce='asdfkjl3kmalkml;xml;mla'
        )
        token = tokens.encode(session, 'notthesecret')
        response = self.client.get('/public', headers={'Authorization': token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         "A 401 exception is passed by the middleware")
