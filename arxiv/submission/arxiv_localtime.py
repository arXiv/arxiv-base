"""Date/time calculations for the arXiv ``localtime``

Business logic of arXiv business days/hours

The submission workflow answered by these values is: "If I submitted a
paper now, when does it freeze, when is it announced, and when is the
announcement after that (if I miss the deadline)?"

"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Holiday

# Timezone of the arXiv business offices (freeze / publish policy is
# expressed in this zone). Port of $ARXIV_OFFICES_BUSINESS_TZ from
# arXiv::Config::MainSite.
BUSINESS_TZ = ZoneInfo("America/New_York")

# Hour of day (in BUSINESS_TZ) at which the daily publish/mailing runs.
# Port of arXiv::Submit::Util::publish_hour_policy (constant 20:00).
PUBLISH_HOUR = 20

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
# Calendar predicates
# --------------------------------------------------------------------------

def is_holiday(t0: date, holidays: frozenset[str]) -> bool:
    """True if ``t0`` (a business-tz calendar date) is an arXiv holiday.

    Port of ``is_holiday_iso8601``. Weekends are *not* holidays here.
    ``holidays`` is the ISO8601 date set from :func:`get_holidays`.
    """
    return t0.isoformat() in holidays


def is_workday(t0: date, holidays: frozenset[str]) -> bool:
    """True if there is a freeze on ``t0``: not a holiday and not a weekend.

    Python ``date.weekday()``: Mon=0 .. Sun=6, so 5/6 are Sat/Sun.
    """
    return not is_holiday(t0, holidays) and t0.weekday() < 5


def is_publish_day(t0: date, holidays: frozenset[str]) -> bool:
    """True if ``t0`` is a publish/mailing day. Port of ``isPublishDay``.

    - Fri/Sat: never a publish day (cron does not run).
    - Sun: a publish day only if the preceding Friday was not a holiday.
    - Mon-Thu: a publish day unless it is a holiday.
    """
    wd = t0.weekday()  # Mon=0 .. Sun=6
    if wd in (4, 5):          # Friday, Saturday
        return False
    if wd == 6:               # Sunday
        friday = t0 - timedelta(days=2)
        return not is_holiday(friday, holidays)
    return not is_holiday(t0, holidays)  # Monday..Thursday


# --------------------------------------------------------------------------
# Policy hours
# --------------------------------------------------------------------------

def freeze_hour_policy(dt: datetime) -> int:
    """Freeze hour (in BUSINESS_TZ) in effect on ``dt``.

    Port of ``freeze_hour_policy``. Freeze was 16:00 through 2017-01-01
    and 14:00 from 2017-01-02 onward.
    """
    if dt.year < 2017 or (dt.year == 2017 and dt.month == 1 and dt.day == 1):
        return 16
    return 14


def publish_hour_policy() -> int:
    """Publish hour (in BUSINESS_TZ). Port of ``publish_hour_policy``."""
    return PUBLISH_HOUR


# --------------------------------------------------------------------------
# Workday walking
# --------------------------------------------------------------------------

def _midnight(t0: date) -> datetime:
    """Start-of-day (00:00) in BUSINESS_TZ for calendar date ``t0``."""
    return datetime(t0.year, t0.month, t0.day, tzinfo=BUSINESS_TZ)


def next_workday(dt: datetime, holidays: frozenset[str]) -> datetime:
    """Advance to the next workday, preserving time of day.

    Port of ``next_workday``: steps forward over holidays and weekends.
    """
    dt_date = dt.date()
    while not is_workday(dt_date, holidays):
        dt_date += timedelta(days=1)
    return dt.replace(year=dt_date.year, month=dt_date.month, day=dt_date.day)


def last_workday(dt: datetime, holidays: frozenset[str]) -> datetime:
    """Step back to the previous workday, preserving time of day.

    Port of ``last_workday``: steps backward over holidays and weekends.
    """
    dt_date = dt.date()
    while not is_workday(dt_date, holidays):
        dt_date -= timedelta(days=1)
    return dt.replace(year=dt_date.year, month=dt_date.month, day=dt_date.day)


# --------------------------------------------------------------------------
# Freeze times
# --------------------------------------------------------------------------

def next_freeze_time(submit_dt: datetime, holidays: frozenset[str]) -> datetime:
    """Next freeze DateTime at/after ``submit_dt``. Port of ``next_freeze_time``.

    Freezes happen only on workdays (holidays and weekends are skipped).
    """
    submit_dt = submit_dt.astimezone(BUSINESS_TZ)

    # Start with the start of the submission day (business tz).
    freeze = _midnight(submit_dt.date())

    # Move to the next day if today's freeze has already passed.
    if submit_dt.hour >= freeze_hour_policy(freeze):
        freeze += timedelta(days=1)

    # Move past holidays / weekends.
    freeze = next_workday(freeze, holidays)

    # Set the freeze hour for the (possibly different) freeze day.
    return freeze.replace(hour=freeze_hour_policy(freeze))


def last_freeze_time(dt: datetime, holidays: frozenset[str]) -> datetime:
    """Most recent freeze at/before ``dt``. Port of ``last_freeze_time``.

    If ``dt`` is exactly the freeze time it returns ``dt`` (the freeze on
    that day), not the previous one -- relied upon by
    :func:`is_between_freeze_and_publish`.
    """
    dt = dt.astimezone(BUSINESS_TZ)
    freeze = _midnight(dt.date())
    if dt.hour < freeze_hour_policy(dt):
        freeze -= timedelta(days=1)
    freeze = last_workday(freeze, holidays)
    return freeze.replace(hour=freeze_hour_policy(freeze))


# --------------------------------------------------------------------------
# Publish / mail times
# --------------------------------------------------------------------------

def next_publish_time(dt: datetime, holidays: frozenset[str]) -> datetime:
    """Next upcoming publish time from ``dt``. Port of ``next_publish_time``.

    NOTE: this is *not* the publish time for a submission made at ``dt``;
    it is the next scheduled mailing. For a submission's publish time use
    :func:`publish_time`.
    """
    dt = dt.astimezone(BUSINESS_TZ)
    publish = datetime(dt.year, dt.month, dt.day, hour=12, tzinfo=BUSINESS_TZ)

    # Move to the next day if the publish hour has already passed.
    if dt.hour >= publish_hour_policy():
        publish += timedelta(days=1)

    while not is_publish_day(publish.date(), holidays):
        publish += timedelta(days=1)

    return publish.replace(hour=publish_hour_policy())


def publish_time(submit_dt: datetime, holidays: frozenset[str]) -> datetime:
    """Publish time for a paper submitted at ``submit_dt``. Port of ``publish_time``.

    Take the submission time, find the next freeze after it, then the next
    publish after that freeze.
    """
    return next_publish_time(next_freeze_time(submit_dt, holidays), holidays)


def is_between_freeze_and_publish(
    now: datetime,
    holidays: frozenset[str],
    last_freeze: datetime | None = None,
    next_publish: datetime | None = None,
) -> bool:
    """True if ``now`` falls between the last freeze and the following publish.

    Port of ``is_between_freeze_and_publish``. A one-minute cushion is added
    to the publish edge to avoid races.
    """
    if last_freeze is None:
        last_freeze = last_freeze_time(now, holidays)
    if next_publish is None:
        next_publish = next_publish_time(last_freeze, holidays)
    next_publish = next_publish + timedelta(minutes=1)
    return last_freeze <= now <= next_publish


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