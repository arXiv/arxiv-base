"""Business-calendar helpers for arXiv's freeze/publish cycle.

Single source of truth for the business timezone and the daily
freeze/publish time calculations, so every consumer computes the same
schedule instead of each keeping its own copy.

The business TZ is a constant (``America/New_York``), not a setting:
arXiv's publish calendar is tied to a specific physical timezone, so
configurability buys nothing and creates a drift hazard.

Holiday-aware functions take an injected ``is_holiday`` callable so
they remain pure / unit-testable; callers pass in a DB-backed callable
(see ``arxiv.schedule.holidays.is_holiday``) that reads
``arXiv_holidays``.

Functions accept an optional ``now`` argument so callers can pass an
explicit timestamp (tests, replays) without monkey-patching ``datetime``.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BUSINESS_TZ = ZoneInfo("America/New_York")

# Freeze occurs at 14:00 (2pm) BUSINESS_TZ daily, weekdays only.
# Reference: lib/arXiv/Submit/Util.pm:348 (freeze_hour_policy)
_FREEZE_HOUR = 14
# Publish (announcement) occurs at 20:00 BUSINESS_TZ.
# Reference: lib/arXiv/Submit/Util.pm:350 (publish_hour_policy)
_PUBLISH_HOUR = 20

HolidayLookup = Callable[[date], bool]


def _never_holiday(_d: date) -> bool:
    return False


def local_date(dt: datetime) -> date:
    """Convert an aware datetime to its date in the business TZ."""
    return dt.astimezone(BUSINESS_TZ).date()


def last_freeze_time(now: datetime | None = None, *, is_holiday: HolidayLookup = _never_holiday) -> datetime:
    """Most recent freeze datetime in the business TZ.

    Freeze is 14:00 weekdays. If ``now`` is before today's freeze the
    previous day's freeze is returned; weekends (and holidays, when
    ``is_holiday`` is passed) fall back further. With the default
    ``is_holiday`` this is a weekends-only walk-back, matching this
    function's original caller (the daily-listing received-window
    line, which doesn't need holiday awareness).

    Reference: lib/arXiv/Submit/Util.pm:310-320 (last_freeze_time),
    Util.pm:220-233 (last_workday).
    """
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)
    candidate = now.date()
    if now.hour < _FREEZE_HOUR:
        candidate -= timedelta(days=1)
    for _ in range(30):
        if is_freeze_day(candidate, is_holiday=is_holiday):
            return datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                _FREEZE_HOUR,
                tzinfo=BUSINESS_TZ,
            )
        candidate -= timedelta(days=1)
    raise RuntimeError("no freeze day within 30 days; holiday lookup likely broken")


def is_freeze_day(d: date, *, is_holiday: HolidayLookup = _never_holiday) -> bool:
    """Return True iff `d` is a freeze day: Mon-Fri AND not a holiday.

    Freezes happen on workdays (no weekends, no holidays).
    Reference: lib/arXiv/Submit/Util.pm:273-295 (next_freeze_time loop)
    + lib/arXiv/Config/Holidays.pm:168-178 (nextWorkDay).
    """
    if d.weekday() >= 5:  # Sat=5, Sun=6
        return False
    return not is_holiday(d)


def is_publish_day(d: date, *, is_holiday: HolidayLookup = _never_holiday) -> bool:
    """Return True iff `d` is a publish (announcement) day.

    Mon-Thu when not a holiday; Sun only when the previous Friday was
    not a holiday. Friday and Saturday are NEVER publish days because
    Friday's freeze publishes on Sunday.
    Reference: lib/arXiv/Config/Holidays.pm:192-210 (isPublishDay).
    """
    wd = d.weekday()  # Mon=0 .. Sun=6
    if wd in (4, 5):  # Friday, Saturday
        return False
    if wd == 6:  # Sunday
        friday = d - timedelta(days=2)
        return not is_holiday(friday)
    # Mon-Thu
    return not is_holiday(d)


def next_freeze_time(now: datetime | None = None, *, is_holiday: HolidayLookup = _never_holiday) -> datetime:
    """Next freeze datetime (14:00 BUSINESS_TZ) on or after ``now``.

    Boundary: strictly before today's 14:00 returns today's freeze;
    at or after 14:00 (``now_et.hour >= 14``) advances to the next
    freeze day. Skips weekends and holidays.
    Reference: lib/arXiv/Submit/Util.pm:273-295 (next_freeze_time),
    matches the perl ``>= freeze_hour_policy`` semantics at line 286.
    """
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)
    candidate = now.date()
    if now.hour >= _FREEZE_HOUR:
        candidate += timedelta(days=1)
    # Bounded scan; perl Holidays.pm:nextWorkDay caps at 30.
    for _ in range(30):
        if is_freeze_day(candidate, is_holiday=is_holiday):
            return datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                _FREEZE_HOUR,
                tzinfo=BUSINESS_TZ,
            )
        candidate += timedelta(days=1)
    raise RuntimeError("no freeze day within 30 days; holiday lookup likely broken")


def next_publish_time(now: datetime | None = None, *, is_holiday: HolidayLookup = _never_holiday) -> datetime:
    """Next publish datetime (20:00 BUSINESS_TZ) on or after ``now``.

    Boundary: strictly before today's 20:00 returns today's publish;
    at or after 20:00 (``now_et.hour >= 20``) advances to the next
    publish day.
    Reference: lib/arXiv/Submit/Util.pm:103-121 (next_publish_time),
    matches the perl ``>= publish_hour_policy`` semantics at line 112.
    """
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)
    candidate = now.date()
    if now.hour >= _PUBLISH_HOUR:
        candidate += timedelta(days=1)
    for _ in range(30):
        if is_publish_day(candidate, is_holiday=is_holiday):
            return datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                _PUBLISH_HOUR,
                tzinfo=BUSINESS_TZ,
            )
        candidate += timedelta(days=1)
    raise RuntimeError("no publish day within 30 days; holiday lookup likely broken")


def last_publish_time(now: datetime | None = None, *, is_holiday: HolidayLookup = _never_holiday) -> datetime:
    """Most recent publish datetime (20:00 BUSINESS_TZ) at or before ``now``.

    The backward-walking counterpart to ``next_publish_time``, for callers
    that need "when did/does the most recently-due publish run start"
    rather than "when is the next one." Holiday-aware, unlike
    ``last_freeze_time``'s simpler weekends-only walk-back (fine for that
    function's one existing caller -- the daily-listing received-window
    line -- but not fine for a caller that must not false-fire on a
    holiday, e.g. production monitoring for a missed publish run).

    Boundary: at or after today's 20:00 returns today's publish time;
    strictly before walks back to the most recent prior publish day.
    """
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)
    candidate = now.date()
    if now.hour < _PUBLISH_HOUR:
        candidate -= timedelta(days=1)
    for _ in range(30):
        if is_publish_day(candidate, is_holiday=is_holiday):
            return datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                _PUBLISH_HOUR,
                tzinfo=BUSINESS_TZ,
            )
        candidate -= timedelta(days=1)
    raise RuntimeError("no publish day within 30 days; holiday lookup likely broken")


def publish_time(submit_dt: datetime | None = None, *, is_holiday: HolidayLookup = _never_holiday) -> datetime:
    """The publish datetime for an article submitted at ``submit_dt``.

    NOT the same as ``next_publish_time``: e.g. for a Sunday-morning
    submission this returns Monday (Sunday's freeze already passed),
    while ``next_publish_time(now=Sunday morning)`` returns Sunday
    evening -- that's the next publish *run*, not the one this
    submission's freeze feeds into.

    Reference: lib/arXiv/Submit/Util.pm:63-76 (publish_time).
    """
    freeze = next_freeze_time(submit_dt, is_holiday=is_holiday)
    return next_publish_time(freeze, is_holiday=is_holiday)


def is_between_freeze_and_publish(now: datetime | None = None, *, is_holiday: HolidayLookup = _never_holiday) -> bool:
    """Whether ``now`` falls between the most recent freeze and the
    publish run it feeds into (inclusive, with a 1-minute buffer past
    publish to avoid a race at the exact boundary).

    True e.g. Friday 14:00 through Sunday 20:01 (Friday's freeze
    publishes Sunday) -- submissions are frozen but not yet announced.

    Reference: lib/arXiv/Submit/Util.pm:376-386 (is_between_freeze_and_publish).
    """
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)
    last_freeze = last_freeze_time(now, is_holiday=is_holiday)
    next_publish = next_publish_time(last_freeze, is_holiday=is_holiday) + timedelta(minutes=1)
    return last_freeze <= now <= next_publish


def compute_pub_yymmdd(now: datetime | None = None) -> str:
    """YYMMDD of the publish day corresponding to the last freeze.

    Mon-Thu freeze -> publish same day (20:00 BUSINESS_TZ).
    Friday freeze -> publish Sunday (Saturday is not a publish day).

    Reference: lib/arXiv/Submit/Util.pm:46-52 (pub_yymmdd).
    """
    freeze = last_freeze_time(now)
    publish_day = freeze
    if freeze.weekday() == 4:  # Friday -> Sunday
        publish_day = freeze + timedelta(days=2)
    publish_time = publish_day.replace(hour=20, minute=0, second=0, microsecond=0)
    return publish_time.strftime("%y%m%d")
