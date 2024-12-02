import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import tempfile
import sqlite3

# Without this import, Base.metadata does not get populated. So it may look doing nothing but do not remove this.
import arxiv.db.models

from .. import Base, LaTeXMLBase, session_factory, _classic_engine as classic_engine

def _make_schemas(db_uri: str):
    db_engine = create_engine(db_uri)

    SessionLocal = sessionmaker(autocommit=False, autoflush=True)
    SessionLocal.configure(bind=db_engine)
    db_session = SessionLocal(autocommit=False, autoflush=True)
    db_session.execute(text('select 1'))

    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    LaTeXMLBase.metadata.drop_all(db_engine)
    LaTeXMLBase.metadata.create_all(db_engine)

    db_session.commit()


def test_db_schema():
    db_uri = os.environ.get('TEST_ARXIV_DB_URI')
    if db_uri is None:
        print("db_uri is not defined")
        return
    _make_schemas(db_uri)


def test_db_schema_sqlite3():
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as tmp:
        filename = tmp.name
    # TIL - you need 4 slashes as the hostname is between 2nd and 3rd slashes
    _make_schemas("sqlite:///" + filename)
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    n_tables = 0
    for row in cur.fetchall():
        # print(row[0])
        n_tables += 1
    conn.close()
    # There are 145 tables on arxiv-production, and 3 LaTexML tables in the db/model.py
    assert n_tables == (145 + 3)
    os.unlink(filename)
