"""Tests for :func:`arxiv.db.configure_db`'s ``creator`` argument.

``creator`` exists for connections that cannot be written as a URI -- the
Cloud SQL Python Connector being the case that motivated it. The caller
passes a dialect-only ``CLASSIC_DB_URI`` plus a zero-argument callable that
returns a live DBAPI connection, and arxiv-base still owns the resulting
engine, models and Session.

sqlite3 stands in for the connector here: it is a real DBAPI whose
``connect`` takes no required arguments, so a creator that returns one
proves the callable is what actually dials, without needing a MySQL server.
"""

from __future__ import annotations

import sqlite3

from sqlalchemy import text

from arxiv.config import Settings
from arxiv.db import configure_db


def _settings(uri: str) -> Settings:
    return Settings(CLASSIC_DB_URI=uri, LATEXML_DB_URI="")


def test_creator_is_used_to_dial() -> None:
    """The engine connects through the callable, not through the URI."""
    calls = []

    def creator():
        calls.append(1)
        return sqlite3.connect(":memory:")

    engine, _ = configure_db(_settings("sqlite://"), creator=creator)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1
    assert calls, "creator was never called -- the URI dialled instead"


def test_creator_reaches_the_database_it_opened() -> None:
    """Not just called: the connection it returns is the one used."""
    shared = sqlite3.connect(":memory:", check_same_thread=False)
    shared.execute("CREATE TABLE marker (v TEXT)")
    shared.execute("INSERT INTO marker VALUES ('from-creator')")
    shared.commit()

    engine, _ = configure_db(_settings("sqlite://"), creator=lambda: shared)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT v FROM marker")).scalar() == "from-creator"


def test_omitting_creator_is_unchanged() -> None:
    """Default stays URI-dialled -- the package-load path must not shift."""
    engine, _ = configure_db(_settings("sqlite://"))
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_creator_applies_to_the_non_sqlite_branch() -> None:
    """The MySQL branch is the real target: a dialect-only URI plus a creator,
    exactly how the Cloud SQL Python Connector is wired.

    The driver is mysqldb, NOT pymysql: ``create_engine`` imports the DBAPI
    eagerly, and mysqlclient (which provides ``MySQLdb``) is a locked main
    dependency of this package while pymysql appears nowhere in poetry.lock.
    A pymysql URL fails in CI with ModuleNotFoundError even though it works
    in environments that happen to have it.

    Asserted on the built engine rather than by connecting: the mysql dialect
    calls ``character_set_name()`` on every new connection, which only a live
    MySQL server provides. What matters here is that the creator reaches the
    pool on this branch too, alongside the branch's pool options.
    """

    def creator():  # never called -- we do not connect
        raise AssertionError("unreachable")

    engine, _ = configure_db(_settings("mysql+mysqldb://"), creator=creator)
    assert engine.dialect.name == "mysql"
    assert engine.pool._creator is creator
    assert engine.pool._recycle == 600  # branch options still applied
