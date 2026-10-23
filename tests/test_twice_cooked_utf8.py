"""
Tests for LegacyUtf8String and LegacyUtf8Text ("twice cooked" utf8).

The legacy app writes utf8 bytes through a latin1 connection into utf8 tables, so the server
re-encodes them and the stored text is double-encoded. These types let a utf8mb4 connection
read and write the same data the legacy app sees.

To run this test:
    pytest tests/test_twice_cooked_utf8.py -v

The MySQL container fixtures are shared with tests/test_utf8_columns.py.
"""
from __future__ import annotations

import logging
from typing import Generator

import pytest
from sqlalchemy import Column, Connection, Engine, Integer, MetaData, Table, select, text
from sqlalchemy.orm import Session

from arxiv.db.column_types import LegacyUtf8String, LegacyUtf8Text
from arxiv.db.legacy_utf8_table import check_legacy_utf8_table_columns_in_db, check_legacy_utf8_tables
from tests.test_utf8_columns import (  # noqa: F401  (fixtures)
    db_engine, db_session,
)

TABLE_NAME = "twice_cooked_test"

SAMPLES = [
    "ASCII only",
    "2-byte: é ñ ü ß",
    "3-byte: 日本語",
    "cp1252 range: Müller – “quoted” €",
    "undefined cp1252 byte: Łukasz",  # UTF-8 C5 81
    "4-byte: \U0001F600",
]

metadata = MetaData()
cooked = Table(
    TABLE_NAME, metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", LegacyUtf8String.column_factory(64)),
    Column("body", LegacyUtf8Text.column_factory()),
    mysql_charset="utf8mb3",
)


@pytest.fixture(scope="module", autouse=True)
def cooked_table(db_engine: Engine) -> Generator[None, None, None]:
    metadata.create_all(db_engine)
    yield
    metadata.drop_all(db_engine)


@pytest.fixture(autouse=True)
def clean_table(db_engine: Engine) -> None:
    with db_engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {TABLE_NAME}"))


# The legacy side is emulated on the server: the legacy latin1 connection sends utf8 bytes that
# MySQL takes as latin1 text, and reads back CONVERT(col USING latin1). Doing it in SQL avoids the
# driver's own idea of "latin1" (MySQLdb uses cp1252, Python's latin1 differs for 0x80-0x9f).

def legacy_insert(conn: Connection, sample: str) -> None:
    conn.execute(
        text(f"INSERT INTO {TABLE_NAME} (body) VALUES (CONVERT(UNHEX(:h) USING latin1))"),
        {"h": sample.encode("utf-8").hex()},
    )


def legacy_read_raw(conn: Connection) -> bytes:
    """The bytes the legacy latin1 connection receives."""
    hexed = conn.execute(text(f"SELECT HEX(CONVERT(body USING latin1)) FROM {TABLE_NAME}")).scalar_one()
    return bytes.fromhex(hexed)


def legacy_read(conn: Connection) -> str:
    """What the legacy app reads: the utf8 bytes it originally wrote."""
    return legacy_read_raw(conn).decode("utf-8")


def test_connection_is_utf8mb4(db_engine: Engine) -> None:
    """The types assume a utf8mb4 connection; fail loudly if the engine default changes."""
    with db_engine.connect() as conn:
        assert conn.execute(text("SELECT @@character_set_connection")).scalar() == "utf8mb4"


def test_table_is_utf8mb3(db_engine: Engine) -> None:
    assert check_legacy_utf8_table_columns_in_db(metadata, db_engine) == []


@pytest.mark.parametrize("sample", SAMPLES)
def test_round_trip(db_session: Session, sample: str) -> None:
    db_session.execute(cooked.insert().values(name=sample[:64], body=sample))
    db_session.commit()
    db_session.expire_all()

    row = db_session.execute(select(cooked.c.name, cooked.c.body)).one()
    assert row.name == sample[:64]
    assert row.body == sample


@pytest.mark.parametrize("sample", SAMPLES)
def test_stored_form_is_double_encoded(db_engine: Engine, db_session: Session, sample: str) -> None:
    """Non-ASCII text is stored double-encoded, as the legacy app leaves it."""
    db_session.execute(cooked.insert().values(body=sample))
    db_session.commit()

    with db_engine.connect() as conn:
        stored = conn.execute(text(f"SELECT body FROM {TABLE_NAME}")).scalar_one()
        assert (stored == sample) == sample.isascii()
        assert legacy_read(conn) == sample


@pytest.mark.parametrize("sample", SAMPLES)
def test_legacy_connection_reads_our_write(db_engine: Engine, db_session: Session, sample: str) -> None:
    db_session.execute(cooked.insert().values(body=sample))
    db_session.commit()

    with db_engine.connect() as conn:
        assert legacy_read(conn) == sample


@pytest.mark.parametrize("sample", SAMPLES)
def test_we_read_legacy_write(db_engine: Engine, db_session: Session, sample: str) -> None:
    with db_engine.begin() as conn:
        legacy_insert(conn, sample)

    assert db_session.execute(select(cooked.c.body)).scalar_one() == sample


def test_plain_utf8_row_is_returned_unchanged(db_engine: Engine, db_session: Session) -> None:
    """A row written as real utf8 (not double-encoded) is not mangled on read."""
    with db_engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {TABLE_NAME} (body) VALUES (:b)"), {"b": "é"})

    assert db_session.execute(select(cooked.c.body)).scalar_one() == "é"


def test_single_encoded_row_is_lossy_for_legacy_until_rewritten(db_engine: Engine, db_session: Session) -> None:
    """A value some writer stored single-encoded (sid 8180083's submitter_name) reads correctly
    here, but a legacy (latin1) reader gets '?' for characters outside latin1. Writing it back
    through the type stores the double-encoded form, which the legacy reader decodes."""
    name = "Oana-Maria-Cătălina Crisan"
    with db_engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {TABLE_NAME} (id, body) VALUES (1, :b)"), {"b": name})
    with db_engine.connect() as conn:
        assert legacy_read_raw(conn) == b"Oana-Maria-C?t?lina Crisan"

    assert db_session.execute(select(cooked.c.body)).scalar_one() == name
    db_session.execute(cooked.update().values(body=name))
    db_session.commit()
    with db_engine.connect() as conn:
        assert legacy_read(conn) == name


def test_none_round_trip(db_session: Session) -> None:
    db_session.execute(cooked.insert().values(name=None, body=None))
    db_session.commit()
    row = db_session.execute(select(cooked.c.name, cooked.c.body)).one()
    assert row.name is None and row.body is None


def test_search_matches_non_ascii(db_session: Session) -> None:
    db_session.execute(cooked.insert().values(name="Müller", body="日本語 paper"))
    db_session.execute(cooked.insert().values(name="Smith", body="plain"))
    db_session.commit()

    assert db_session.execute(select(cooked.c.name).where(cooked.c.name == "Müller")).scalars().all() == ["Müller"]
    assert db_session.execute(select(cooked.c.name).where(cooked.c.body.contains("日本"))).scalars().all() == ["Müller"]
    assert db_session.execute(select(cooked.c.name).where(cooked.c.name.startswith("Mü"))).scalars().all() == ["Müller"]


def test_check_warns_on_non_utf8_table(caplog: pytest.LogCaptureFixture) -> None:
    bad = MetaData()
    Table("latin1_table", bad, Column("t", LegacyUtf8Text.column_factory()), mysql_charset="latin1")
    with caplog.at_level(logging.WARNING, logger="arxiv.db.legacy_utf8_table"):
        problems = check_legacy_utf8_tables(bad)
    assert len(problems) == 1 and "latin1_table" in problems[0]
    assert "latin1_table" in caplog.text


def test_check_is_quiet_for_utf8_table() -> None:
    assert check_legacy_utf8_tables(metadata) == []
