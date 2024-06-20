"""Testing helpers."""
from contextlib import contextmanager

from flask import Flask

from arxiv.config import Settings
from arxiv.db.models import configure_db
from .. import util


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
            with util.transaction() as session:
                yield session
        finally:
            if drop:
                util.drop_all(engine)
