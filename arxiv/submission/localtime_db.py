"""Database-backed half of the arXiv ``localtime`` calculations.

Everything here needs a live :class:`~sqlalchemy.orm.Session`: the holiday
calendar comes out of the ``arXiv_holidays`` table, and the aggregate the
localtime page renders is built on top of it.

It is a separate module from :mod:`arxiv.submission.arxiv_localtime` because
importing ``arxiv.db`` has a side effect -- :func:`arxiv.db.configure_db`
runs at package load and builds an engine from ``CLASSIC_DB_URI``. Keeping
that out of the pure calendar module means asking "is today a publish day?"
never requires a configured database, and a caller that connects by other
means (the Cloud SQL Python Connector, say) can use the calendar without
arxiv.db trying to dial for it.

The pure date arithmetic lives next door and is imported from there.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Holiday
from .arxiv_localtime import (
    BUSINESS_TZ,
    freeze_hour_policy,
    is_between_freeze_and_publish,
    last_freeze_time,
    next_freeze_time,
    next_publish_time,
    publish_time,
)


def get_holidays(
    session: Session,
    start_date: date | Callable[[], date] | None = date.today,
    end_date: date | None = None,
) -> frozenset[str]:
    """Fetch the arXiv holiday calendar as ISO8601 date strings.

    Holidays are weekdays with *no* freeze (and hence no subsequent
    mailing/announcement). Read from the ``arXiv_holidays`` table via the
    :class:`~arxiv.db.models.Holiday` model. Weekends are handled
    separately and are not stored here.

    The result is restricted to ``start_date <= freeze_skip_date <= end_date``.

    ``start_date`` (inclusive lower bound):
      - a :class:`datetime.date` -- use that date;
      - a zero-arg callable returning a date -- called to resolve the bound
        (the default, ``date.today``, means "today"). A callable is used as
        the default so that ``None`` is free to mean "no lower bound";
      - ``None`` -- no lower bound.

    ``end_date`` (inclusive upper bound): a date, or ``None`` for no upper
    bound (the default).

    Note: calculations that walk *backwards* over the calendar
    (:func:`last_freeze_time`, :func:`is_between_freeze_and_publish`) can
    reference a holiday a few days before ``now``; pass an earlier
    ``start_date`` if you rely on those.
    """
    stmt = select(Holiday.freeze_skip_date)
    if start_date is not None:
        if callable(start_date):
            start_date = start_date()
        stmt = stmt.where(Holiday.freeze_skip_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(Holiday.freeze_skip_date <= end_date)
    dates = session.scalars(stmt).all()
    return frozenset(holiday_date.isoformat() for holiday_date in dates)


# --------------------------------------------------------------------------
# Aggregate result
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LocalTimeInfo:
    """All date/time values the localtime page needs, no presentation.

    Attributes
    ----------
    now:
        Reference time, in BUSINESS_TZ.
    arxiv_tz:
        Timezone abbreviation in effect at ``now`` (e.g. ``"EST"`` / ``"EDT"``).
    freeze_hour:
        Freeze hour policy (BUSINESS_TZ hour) in effect at ``now``.
    next_freeze:
        Next submission deadline (freeze) at/after ``now``.
    duration_to_freeze:
        ``next_freeze - now``.
    next_mail:
        Mailing that a submission made now would be announced in -- i.e.
        the publish after ``next_freeze``.
    subsequent_mail:
        The mailing after ``next_mail`` (what happens if the deadline is
        missed).
    publish_time_now:
        Publish time for a submission made exactly at ``now``, adjusted for
        the freeze/publish window (mirrors the JSON endpoint's ``next_mail``).
    """

    now: datetime
    arxiv_tz: str
    freeze_hour: int
    next_freeze: datetime
    duration_to_freeze: timedelta
    next_mail: datetime
    subsequent_mail: datetime
    publish_time_now: datetime


def compute_localtime(session: Session,
                      now: datetime | None = None) -> LocalTimeInfo:
    """Compute every localtime value for ``now`` (defaults to current time).

    ``session`` is used once to load the holiday calendar via
    :func:`get_holidays`. ``now`` may be naive or timezone-aware; it is
    converted to BUSINESS_TZ. Returns a :class:`LocalTimeInfo`; rendering
    is the caller's job.
    """
    if now is None:
        now = datetime.now(tz=BUSINESS_TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)

    # Load holidays from ``now`` forward. The backward-looking window
    # (last_freeze / is_between_freeze_and_publish) starts at the previous
    # workday, so include a few days before ``now`` to cover a holiday
    # immediately preceding it.
    holidays = get_holidays(session, start_date=now.date() - timedelta(days=14))

    next_freeze = next_freeze_time(now, holidays)
    duration_to_freeze = next_freeze - now

    # Mailing after the next freeze, and the one after that.
    next_mail = next_publish_time(next_freeze, holidays)
    subsequent_mail = next_publish_time(next_mail + timedelta(minutes=1), holidays)

    # Publish time for a submission made "now", with the freeze/publish
    # window adjustment used by the JSON endpoint: while between a freeze
    # and its publish, report the publish for a submission made just before
    # that last freeze.
    pub_now = publish_time(now, holidays)
    if is_between_freeze_and_publish(now, holidays):
        right_before_last_freeze = last_freeze_time(now, holidays) - timedelta(seconds=1)
        pub_now = publish_time(right_before_last_freeze, holidays)

    return LocalTimeInfo(
        now=now,
        arxiv_tz=now.strftime("%Z"),
        freeze_hour=freeze_hour_policy(now),
        next_freeze=next_freeze,
        duration_to_freeze=duration_to_freeze,
        next_mail=next_mail,
        subsequent_mail=subsequent_mail,
        publish_time_now=pub_now,
    )


# Cache for :func:`compute_localtime_cached`, keyed on the current wall-clock
# minute ("YYYY-MM-DD HH:MM"). One underlying compute_localtime() call per
# distinct minute: recompute only when the minute rolls over.
_cache_lock = threading.Lock()
_cache: tuple[str, LocalTimeInfo] | None = None


def _minute_key(dt: datetime) -> str:
    """Wall-clock minute bucket for ``dt`` (seconds dropped)."""
    return dt.strftime("%Y-%m-%d %H:%M")


def compute_localtime_cached(session: Session,
                             now: datetime | None = None) -> LocalTimeInfo:
    """Minute-cached :func:`compute_localtime`.

    Same signature and return value as :func:`compute_localtime`, but the
    underlying computation runs at most once per wall-clock minute: within a
    given minute (``HH:MM``) every call returns the same cached
    :class:`LocalTimeInfo`, and it is recomputed only when the minute rolls
    over. Thread-safe.

    Only the live path (``now is None``) is cached. When an explicit ``now``
    is passed the result is deterministic for that timestamp, so it bypasses
    the cache and calls :func:`compute_localtime` directly -- otherwise the
    cache could return a value computed for a different ``now``.
    """
    if now is not None:
        return compute_localtime(session, now)

    global _cache
    with _cache_lock:
        key = _minute_key(datetime.now(tz=BUSINESS_TZ))
        if _cache is not None and _cache[0] == key:
            return _cache[1]
        result = compute_localtime(session, None)
        _cache = (key, result)
        return result
