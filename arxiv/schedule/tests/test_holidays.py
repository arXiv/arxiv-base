"""Tests for the shared holiday lookup.

An in-memory SQLite ``arXiv_holidays`` table (created from the real
``Holiday`` model, so schema drift would fail loud) stands in for the
classic DB.
"""

from __future__ import annotations

from datetime import date, datetime

from arxiv.db.models import Base, Holiday
from arxiv.schedule.holidays import is_holiday
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _engine_with_holidays(*holidays: str):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[Holiday.__table__])
    with engine.begin() as conn:
        for d in holidays:
            conn.execute(
                Holiday.__table__.insert().values(
                    freeze_skip_date=date.fromisoformat(d),
                    created_by=1,
                    created_at=datetime(2026, 1, 1),
                )
            )
    return engine


def test_is_holiday_true_for_seeded_date() -> None:
    engine = _engine_with_holidays("2026-12-25")
    with engine.connect() as conn:
        assert is_holiday(conn, date(2026, 12, 25)) is True


def test_is_holiday_false_for_other_date() -> None:
    engine = _engine_with_holidays("2026-12-25")
    with engine.connect() as conn:
        assert is_holiday(conn, date(2026, 12, 24)) is False


def test_is_holiday_false_with_no_rows() -> None:
    engine = _engine_with_holidays()
    with engine.connect() as conn:
        assert is_holiday(conn, date(2026, 12, 25)) is False


def test_is_holiday_accepts_a_session_not_just_a_connection() -> None:
    """The whole point of accepting a Session as well as a Connection is
    that a caller with an ORM session already open doesn't need a second
    connection.
    """
    engine = _engine_with_holidays("2026-12-25")
    session = sessionmaker(bind=engine)()
    try:
        assert is_holiday(session, date(2026, 12, 25)) is True
        assert is_holiday(session, date(2026, 12, 26)) is False
    finally:
        session.close()
