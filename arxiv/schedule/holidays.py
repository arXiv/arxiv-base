"""Shared read-only holiday lookup against ``arXiv_holidays``.

One row per date in America/New_York on which no freeze and no
announcement run; PK column ``freeze_skip_date``. Backed by the
``Holiday`` model in ``arxiv.db.models`` and seeded by
``arxiv_holidays_seed.sql``, kept in sync with the perl
``Config/Holidays.pm`` array via dual-write until the perl side
migrates.

A single source of truth so every consumer of ``calendar.py``'s
``is_holiday`` callable reads the same table the same way, instead of
each growing its own copy.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from arxiv.db.models import Holiday


def is_holiday(conn: Connection | Session, d: date) -> bool:
    """Whether ``d`` is a row in ``arXiv_holidays``.

    ``conn`` accepts either an Engine ``Connection`` or an ORM ``Session``
    -- both expose the same ``.execute(select(...))`` shape for this
    single indexed point select, so a caller with either already open
    can reuse this without opening a second connection.

    No caching: callers here fire a handful of times per day and this is
    a single indexed point select. A no-cache implementation makes ops
    updates to the DB immediately authoritative.
    """
    stmt = select(Holiday.freeze_skip_date).where(Holiday.freeze_skip_date == d).limit(1)
    return conn.execute(stmt).first() is not None
