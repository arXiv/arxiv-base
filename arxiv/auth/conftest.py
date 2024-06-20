import pytest
import os
# os.environ['CLASSIC_DB_URI'] = 'sqlite:///:memory:'

from flask import Flask

from ..base import Base
from ..config import Settings
from ..base.middleware import wrap
from ..db.models import configure_db

from ..auth.arxiv_auth.auth import Auth
from ..auth.arxiv_auth.auth.middleware import AuthMiddleware


@pytest.fixture()
def app():

    app = Flask('test_auth_app')
    app.config['CLASSIC_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['CLASSIC_SESSION_HASH'] = f'fake set in {__file__}'
    app.config['SESSION_DURATION'] = f'fake set in {__file__}'
    app.config['CLASSIC_COOKIE_NAME'] = f'fake set in {__file__}'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['AUTH_UPDATED_SESSION_REF'] = True
    settings = Settings (
        CLASSIC_DB_URI = 'sqlite:///test.db',
        LATEXML_DB_URI = None
    )
    engine, _ = configure_db(settings)
    app.config['DB_ENGINE'] = engine

    Base(app)

    Auth(app)
    wrap(app, [AuthMiddleware])


    return app


@pytest.fixture()
def request_context(app):
    yield app.test_request_context()
