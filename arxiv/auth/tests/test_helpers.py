"""Tests for :mod:`.helpers`."""

from unittest import TestCase, mock
import os
import logging

from flask import Flask

from arxiv import status
from arxiv.config import Settings
from arxiv.db.models import configure_db
from arxiv.base import Base
from arxiv.base.middleware import wrap

from .. import auth, helpers, legacy
from ..auth.middleware import AuthMiddleware
from ..auth.scopes import VIEW_SUBMISSION, CREATE_SUBMISSION, EDIT_SUBMISSION


class TestGenerateToken(TestCase):
    """Tests for :func:`.helpers.generate_token`."""

    def test_token_is_usable(self):
        """Verify that :func:`.helpers.generate_token` makes usable tokens."""
        os.environ['JWT_SECRET'] = 'thesecret'
        scope = [VIEW_SUBMISSION, EDIT_SUBMISSION, CREATE_SUBMISSION]
        token = helpers.generate_token("1234", "user@foo.com", "theuser",
                                       scope=scope)

        app = Flask('test')
        app.config['CLASSIC_SESSION_HASH'] = 'foohash'
        app.config['CLASSIC_COOKIE_NAME'] = 'tapir_session_cookie'
        app.config['SESSION_DURATION'] = '36000'
        app.config['AUTH_UPDATED_SESSION_REF'] = True

        app.config.update({
            'JWT_SECRET': 'thesecret',
        })

        settings = Settings(
                        CLASSIC_DB_URI='sqlite:///:memory:',
                        LATEXML_DB_URI=None)

        configure_db (settings)

        Base(app)
        auth.Auth(app)
        wrap(app, [AuthMiddleware])

        @app.route('/')
        @auth.decorators.scoped(EDIT_SUBMISSION)
        def protected():
            return "this is protected"

        client = app.test_client()
        with app.app_context():
            response = client.get('/')
            self.assertEqual(response.status_code,
                             status.HTTP_401_UNAUTHORIZED)

            response = client.get('/', headers={'Authorization': token})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
