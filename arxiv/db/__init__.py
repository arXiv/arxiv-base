"""This is the primary SQLAlchemy implementation of the main arXiv database.

To use this in a simple non-flask non-fastapi script do:

from arxiv.db import get_db

with get_db() as session:
    session.execute(
        select(...)
    )

To use this in flask just do:

from arxiv.db import session

session.execute(
    select(...)
)

To use this with fastapi do:

with get_db() as session:
    session.execute(
        select(...)
    )

    
for writing within a transaction in any type of app do:

from arxiv.db import transaction

with transaction() as session:
    session.add(...)
"""
import logging
import json
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager

from flask.globals import app_ctx
from flask import has_app_context

from sqlalchemy import Engine, MetaData
from sqlalchemy.event import listens_for
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase

from ..config import settings

metadata = MetaData()

class Base(DeclarativeBase):
    metadata=metadata

class LaTeXMLBase(DeclarativeBase):
    metadata=metadata

logger = logging.getLogger(__name__)


SessionLocal = sessionmaker(autoflush=False)
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


session = scoped_session(SessionLocal, scopefunc=_scope_id)
"""`session` is a per thread proxy to a session created by `arxiv.db.SessionLocal` (which is a `sessionmaker`)"""

def get_engine () -> Engine:
    return SessionLocal().get_bind(Base)

@contextmanager
def get_db ():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def transaction ():
    in_flask = True if has_app_context() else False
    db = session if in_flask else SessionLocal()
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
