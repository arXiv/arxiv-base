"""Shared pytest fixtures for the ``tests`` tree.

The arXiv ``localtime`` unit tests (:mod:`tests.unit.test_arxiv_localtime`)
need two things:

* a database session seeded with a known arXiv holiday calendar, so the
  DB-backed helpers (:func:`~arxiv.submission.arxiv_localtime.get_holidays`,
  :func:`~arxiv.submission.arxiv_localtime.compute_localtime`) can be exercised
  end to end; and
* the same calendar as a plain ``frozenset`` of ISO8601 strings, so the pure
  calendar/policy functions can be tested without touching a database.

The calendar below is fixed and deterministic on purpose. The tests must never
depend on the real wall clock ("now"), so every date here is a concrete
constant and every test injects its own ``now``.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Importing the models module populates ``Base.metadata`` with every table.
import arxiv.db.models  # noqa: F401
from arxiv.db import Base
from arxiv.db.models import Holiday

# --------------------------------------------------------------------------
# The fixed holiday calendar used by the localtime tests.
#
# Each entry is (ISO8601 date, weekday, why-it-matters-for-a-test). The weekday
# spread is deliberate so the tests can showcase every branch of the business
# rules:
#
#   2025-01-01  Wed   a mid-week holiday (New Year's Day)
#   2025-01-20  Mon   a Monday holiday right after a weekend (MLK Day)
#   2025-07-04  Fri   a *Friday* holiday -- drives the "Sunday is a publish
#                     day only if the preceding Friday was a workday" rule
#   2025-11-27  Thu   Thanksgiving
#   2025-12-25  Thu   Christmas
# --------------------------------------------------------------------------
HOLIDAY_DATES: tuple[date, ...] = (
    date(2025, 1, 1),
    date(2025, 1, 20),
    date(2025, 7, 4),
    date(2025, 11, 27),
    date(2025, 12, 25),
)

# ``created_at`` is NOT NULL with a DB server default that sqlite does not
# supply, so seed rows carry an explicit fixed timestamp.
_SEED_CREATED_AT = datetime(2024, 1, 1, 0, 0, 0)


@pytest.fixture
def holidays() -> frozenset[str]:
    """The fixed holiday calendar as an ISO8601 string set.

    This is exactly what :func:`~arxiv.submission.arxiv_localtime.get_holidays`
    returns, but with no database involved -- for testing the pure
    calendar/policy functions.
    """
    return frozenset(holiday.isoformat() for holiday in HOLIDAY_DATES)


@pytest.fixture
def db_session() -> Iterator[Session]:
    """A throwaway in-memory sqlite session with the full arXiv schema.

    Function-scoped: each test gets a fresh, empty database.
    """
    engine = create_engine("sqlite://")  # in-memory
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=True, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def seeded_session(db_session: Session) -> Session:
    """An in-memory session pre-loaded with :data:`HOLIDAY_DATES`."""
    for holiday_date in HOLIDAY_DATES:
        db_session.add(Holiday(
            freeze_skip_date=holiday_date,
            description=f"test holiday {holiday_date.isoformat()}",
            created_at=_SEED_CREATED_AT,
            created_by=1,
        ))
    db_session.commit()
    return db_session
