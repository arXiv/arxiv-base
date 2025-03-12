"""This is the primary SQLAlchemy implementation of the main arXiv database.

To use this in a simple non-flask non-fastapi script do:

from arxiv.db import Session

with Session() as session:
    session.execute(
        select(...)
    )

To use this in flask just do:

from arxiv.db import Session

Session.execute(
    select(...)
)

To use this with fastapi do:

with Session() as session:
    session.execute(
        select(...)
    )

    
for writing within a transaction in any type of app do:

from arxiv.db import transaction

with transaction() as session:
    session.add(...)

Or just do it in a normal transaction:

with Session() as session:
   session.add(...)
   session.commit()


"""
import logging
import json
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Tuple, Optional

try:
    from flask.globals import app_ctx
    from flask import has_app_context, Flask
except ImportError:
    def has_app_context():
        return False

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.event import listens_for
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase

from ..config import settings, Settings

metadata = MetaData()
latexml_metadata = MetaData()
_latexml_engine: Engine = None
_classic_engine: Engine = None

class Base(DeclarativeBase):
    metadata=metadata

class LaTeXMLBase(DeclarativeBase):
    metadata=latexml_metadata

logger = logging.getLogger(__name__)


session_factory = sessionmaker(autoflush=False)
"""`sessionmaker` is the SQLAlchemy class that provides a `sqlalchemy.orm.Session` based on how it is configured. 

It may be used as a `sqlalchemy.orm.Session`. 

Calling `SessionLocal.configure()` will alter all future sessions accessed via `arxiv.db.SessionLocal` or `arxiv.db.session`"""


def _scope_id () -> int:
    """Gets an ID used as a key to the sessions from the scopped_session registry.
    `sqlalchemy.orm.Session` objects are NOT thread safe, but we are using `arxiv.db.session` as if were thread safe.
    This works by `scopped_session` returning a proxy/registry that uses a different session based on
    what thread is running.
    See https://docs.sqlalchemy.org/en/20/orm/contextual.html#thread-local-scope
    """
    if has_app_context():
        # This piece of code is crucial to making sure sqlalchemy sessions work in flask
        # It is the same as the flask_sqlalchemy implementation
        # See: https://github.com/pallets-eco/flask-sqlalchemy/blob/42a36a3cb604fd39d81d00b54ab3988bbd0ad184/src/flask_sqlalchemy/session.py#L109
        return id(app_ctx._get_current_object())
    else:
        return int(threading.current_thread().ident)


Session = scoped_session(session_factory, scopefunc=_scope_id)
"""`Session` is a per thread proxy to a session created by `arxiv.db.SessionLocal` (which is a `sessionmaker`)

Calling `Session()` will return a `sqlalchemy.orm.Session`

It should be used like:

    from arxiv.db import Session
    ...
    with Session() as session:
        session.add(...)
        session.commit()
"""


@contextmanager
def transaction ():
    in_flask = True if has_app_context() else False
    db = Session if in_flask else session_factory()
    try:
        yield db

        if db.new or db.dirty or db.deleted:
            db.commit()
    except Exception as e:
        logger.warning(f'Commit failed, rolling back', exc_info=1)
        db.rollback()
        raise
    finally:
        if not in_flask:
            db.close()


def config_query_timing(engine: Engine, slightly_long_sec: float, long_sec: float):
    @listens_for(engine, "before_cursor_execute")
    def _record_query_start (conn, cursor, statement, parameters, context, executemany):
        conn.info['query_start'] = datetime.now()

    @listens_for(engine, "after_cursor_execute")
    def _calculate_query_run_time (conn, cursor, statement, parameters, context, executemany):
        if conn.info.get('query_start'):
            delta: timedelta = (datetime.now() - conn.info['query_start'])
            query_time = delta.seconds+(delta.microseconds/1000000)
            if query_time > slightly_long_sec and query_time < long_sec:
                log = dict(
                    severity="INFO",
                    message=f"Slightly long query",
                    query_seconds=query_time,
                    query=str(statement)
                )
                print (json.dumps(log))
            elif query_time >= long_sec:
                log = dict(
                    severity="WARNING",
                    message=f"Very long query",
                    query_seconds=query_time,
                    query=str(statement)
                )
                print (json.dumps(log))


def configure_db (base_settings: Settings) -> Tuple[Engine, Optional[Engine]]:
    if 'sqlite' in base_settings.CLASSIC_DB_URI:
        engine = create_engine(base_settings.CLASSIC_DB_URI)
        if base_settings.LATEXML_DB_URI:
            latexml_engine = create_engine(base_settings.LATEXML_DB_URI)
        else:
            latexml_engine = None
    else:
        engine = create_engine(base_settings.CLASSIC_DB_URI,
                        echo=base_settings.ECHO_SQL,
                        isolation_level=base_settings.CLASSIC_DB_TRANSACTION_ISOLATION_LEVEL,
                        pool_recycle=600,
                        max_overflow=(base_settings.REQUEST_CONCURRENCY - 5), # max overflow is how many + base pool size, which is 5 by default
                        pool_pre_ping=base_settings.POOL_PRE_PING)
        if base_settings.LATEXML_DB_URI:
            stmt_timeout: int = max(base_settings.LATEXML_DB_QUERY_TIMEOUT, 1)
            latexml_engine = create_engine(base_settings.LATEXML_DB_URI,
                                    connect_args={"options": f"-c statement_timeout={stmt_timeout}s"},
                                    echo=base_settings.ECHO_SQL,
                                    isolation_level=base_settings.LATEXML_DB_TRANSACTION_ISOLATION_LEVEL,
                                    pool_recycle=600,
                                    max_overflow=(base_settings.REQUEST_CONCURRENCY - 5),
                                    pool_pre_ping=base_settings.POOL_PRE_PING)
        else:
            latexml_engine = None

    global _classic_engine
    global _latexml_engine
    _classic_engine = engine
    _latexml_engine = latexml_engine
    return engine, latexml_engine


# Configure the engine at package load time from env vars.
_classic_engine, _latexml_engine = configure_db(settings)


def init(settings: Settings=settings) -> None:
    """Reset up with new `settings` for the db engines AND models.

    This uses the values from `settings`. """
    # configure_db was called at package load, but need to call again to change
    configure_db(settings)

    # late import of arxiv.db.models to avoid loops
    from arxiv.db.models import configure_db_engine
    configure_db_engine(_classic_engine, _latexml_engine)

