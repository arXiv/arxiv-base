"""Date/time calculations for the arXiv ``localtime``

Business logic of arXiv business days/hours

The submission workflow answered by these values is: "If I submitted a
paper now, when does it freeze, when is it announced, and when is the
announcement after that (if I miss the deadline)?"

Pure date arithmetic: every function here takes the holiday calendar as a
``frozenset`` of ISO8601 date strings and touches no database, so importing
this module never pulls in ``arxiv.db`` (whose package load builds an engine
from ``CLASSIC_DB_URI``). Loading the calendar, and the aggregate the
localtime page renders, live in :mod:`arxiv.submission.localtime_db`.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# Timezone of the arXiv business offices (freeze / publish policy is
# expressed in this zone). Port of $ARXIV_OFFICES_BUSINESS_TZ from
# arXiv::Config::MainSite.
BUSINESS_TZ = ZoneInfo("America/New_York")

# Hour of day (in BUSINESS_TZ) at which the daily publish/mailing runs.
# Port of arXiv::Submit::Util::publish_hour_policy (constant 20:00).
PUBLISH_HOUR = 20

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


def last_publish_time(dt: datetime, holidays: frozenset[str]) -> datetime:
    """Most recent publish time at/before ``dt``.

    The backward-walking counterpart to :func:`next_publish_time`, answering
    "when was the mailing that should have run most recently" rather than
    "when is the next one". Used to detect a publish run that never started.

    Boundary: at/after today's 20:00 on a publish day returns today's publish
    time; strictly before it walks back to the most recent prior publish day.
    """
    dt = dt.astimezone(BUSINESS_TZ)
    publish = _midnight(dt.date())
    if dt.hour < publish_hour_policy():
        publish -= timedelta(days=1)

    while not is_publish_day(publish.date(), holidays):
        publish -= timedelta(days=1)

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


def pub_yymmdd(dt: datetime, holidays: frozenset[str]) -> str:
    """``YYMMDD`` of the publish day belonging to the freeze most recently
    passed at ``dt``. Port of ``pub_yymmdd``.

    This is the mailing a paper frozen in the current cycle lands in, so it
    is *not* :func:`last_publish_time`: a Friday freeze announces on the
    following Sunday, two days after a mailing that already ran on Thursday.
    """
    return next_publish_time(
        last_freeze_time(dt, holidays), holidays
    ).strftime("%y%m%d")
