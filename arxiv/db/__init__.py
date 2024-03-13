"""
This is the primary SQLAlchemy implementation of the main arXiv database 
"""
from typing import Generator
import logging
from contextlib import contextmanager

from flask.globals import app_ctx
from flask import has_app_context

from sqlalchemy import create_engine, MetaData, String
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase


from ..config import settings

metadata = MetaData()

class Base(DeclarativeBase):
    metadata=metadata

class LaTeXMLBase(DeclarativeBase):
    metadata=metadata

logger = logging.getLogger(__name__)

engine = create_engine(settings.CLASSIC_DB_URI,
                       echo=settings.ECHO_SQL)
latexml_engine = create_engine(settings.LATEXML_DB_URI,
                               echo=settings.ECHO_SQL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

def _app_ctx_id () -> int:
    return id(app_ctx._get_current_object())

session = scoped_session(SessionLocal, scopefunc=_app_ctx_id)

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
        logger.warn(f'Commit failed, rolling back', exc_info=1)
        db.rollback()
    finally:
        if not in_flask:
            db.close()