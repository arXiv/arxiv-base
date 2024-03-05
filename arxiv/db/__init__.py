"""
This is the primary SQLAlchemy implementation of the main arXiv database 
"""
from typing import Generator
import logging
from contextlib import contextmanager

from flask import current_app

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.orm import declarative_base

from ..config import (
    CLASSIC_DB_URI,
    ECHO_SQL,
    LATEXML_DB_URI
)

metadata = MetaData()
Base = declarative_base(metadata=metadata)
LaTeXMLBase = declarative_base(metadata=metadata)

logger = logging.getLogger(__name__)

engine = create_engine(CLASSIC_DB_URI,
                       echo=ECHO_SQL)
latexml_engine = create_engine(LATEXML_DB_URI,
                               echo=ECHO_SQL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
SessionLocal.configure(binds={
    Base: engine,
    LaTeXMLBase: latexml_engine,
})

def _app_ctx_id () -> int:
    return id(current_app._get_current_object())

session = scoped_session(SessionLocal, scopefunc=_app_ctx_id)

@contextmanager
def get_db () -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def transaction () -> Generator[Session, None, None]:
    in_flask = True if current_app else False
    db = session if in_flask else SessionLocal() 
    try:
        yield db

        if db.new or db.dirty or db.deleted:
            db.commit()
    except Exception as e:
        logger.warn(f'Commit failed, rolling back', exc_info=1)
        db.rollback()
    finally:
        if not in_flask:
            db.close()