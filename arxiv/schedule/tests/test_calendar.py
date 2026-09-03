"""Tests for the holiday-aware calendar helpers.

Mirrors the perl semantics in arxiv-lib.git/lib/arXiv/Submit/Util.pm
(next_freeze_time, next_publish_time) and Holidays.pm (isPublishDay).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from arxiv.schedule.calendar import (
    BUSINESS_TZ,
    is_between_freeze_and_publish,
    is_freeze_day,
    is_publish_day,
    last_freeze_time,
    last_publish_time,
    next_freeze_time,
    next_publish_time,
    publish_time,
)

ET = BUSINESS_TZ


def _make_lookup(*holidays: str):
    holiday_set = {date.fromisoformat(d) for d in holidays}
    return lambda d: d in holiday_set


# 2026-04-27 is a Monday, 2026-04-28 Tue, ..., 2026-05-01 Fri, 2026-05-02 Sat,
# 2026-05-03 Sun.


def test_is_freeze_day_weekday_no_holiday() -> None:
    no_holidays = _make_lookup()
    assert is_freeze_day(date(2026, 4, 27), is_holiday=no_holidays)  # Mon
    assert is_freeze_day(date(2026, 5, 1), is_holiday=no_holidays)  # Fri


def test_is_freeze_day_weekend() -> None:
    no_holidays = _make_lookup()
    assert not is_freeze_day(date(2026, 5, 2), is_holiday=no_holidays)  # Sat
    assert not is_freeze_day(date(2026, 5, 3), is_holiday=no_holidays)  # Sun


def test_is_freeze_day_holiday() -> None:
    holidays = _make_lookup("2026-04-27")
    assert not is_freeze_day(date(2026, 4, 27), is_holiday=holidays)


def test_is_publish_day_mon_thu() -> None:
    no_holidays = _make_lookup()
    assert is_publish_day(date(2026, 4, 27), is_holiday=no_holidays)  # Mon
    assert is_publish_day(date(2026, 4, 30), is_holiday=no_holidays)  # Thu


def test_is_publish_day_friday_is_never() -> None:
    """Friday's freeze publishes on Sunday; Friday itself is not a publish day."""
    no_holidays = _make_lookup()
    assert not is_publish_day(date(2026, 5, 1), is_holiday=no_holidays)


def test_is_publish_day_saturday_is_never() -> None:
    no_holidays = _make_lookup()
    assert not is_publish_day(date(2026, 5, 2), is_holiday=no_holidays)


def test_is_publish_day_sunday_after_non_holiday_friday() -> None:
    no_holidays = _make_lookup()
    assert is_publish_day(date(2026, 5, 3), is_holiday=no_holidays)


def test_is_publish_day_sunday_after_holiday_friday() -> None:
    """If Friday is a holiday, the Sunday slot is skipped (publishes Monday)."""
    holidays = _make_lookup("2026-05-01")  # Fri holiday
    assert not is_publish_day(date(2026, 5, 3), is_holiday=holidays)


def test_is_publish_day_holiday_weekday() -> None:
    holidays = _make_lookup("2026-04-27")
    assert not is_publish_day(date(2026, 4, 27), is_holiday=holidays)


# last_freeze_time --------------------------------------------------------------


def test_last_freeze_at_cutoff_returns_today() -> None:
    now = datetime(2026, 4, 27, 14, 0, tzinfo=ET)  # Mon exactly 14:00
    out = last_freeze_time(now)
    assert out == datetime(2026, 4, 27, 14, tzinfo=ET)


def test_last_freeze_before_cutoff_walks_back_to_prior_day() -> None:
    now = datetime(2026, 4, 27, 13, 59, tzinfo=ET)  # Mon before cutoff
    out = last_freeze_time(now)
    assert out == datetime(2026, 4, 24, 14, tzinfo=ET)  # prior Friday


def test_last_freeze_skips_weekend() -> None:
    now = datetime(2026, 5, 2, 10, 0, tzinfo=ET)  # Sat, before cutoff
    out = last_freeze_time(now)
    assert out == datetime(2026, 5, 1, 14, tzinfo=ET)  # Fri


def test_last_freeze_default_ignores_holiday() -> None:
    """Weekends-only walk-back by default -- matches the pre-existing
    daily-listing caller, which doesn't pass ``is_holiday``."""
    holidays = _make_lookup("2026-05-01")  # Fri holiday
    now = datetime(2026, 5, 2, 10, 0, tzinfo=ET)  # Sat, before cutoff
    out = last_freeze_time(now)  # no is_holiday passed
    assert out == datetime(2026, 5, 1, 14, tzinfo=ET)  # still lands on the holiday Friday


def test_last_freeze_skips_holiday_when_asked() -> None:
    holidays = _make_lookup("2026-05-01")  # Fri holiday
    now = datetime(2026, 5, 2, 10, 0, tzinfo=ET)  # Sat, before cutoff
    out = last_freeze_time(now, is_holiday=holidays)
    assert out == datetime(2026, 4, 30, 14, tzinfo=ET)  # prior Thu


# next_freeze_time -------------------------------------------------------------


def test_next_freeze_before_today_returns_today() -> None:
    # Mon 2026-04-27 13:59 ET — still before 14:00 cutoff.
    now = datetime(2026, 4, 27, 13, 59, 0, tzinfo=ET)
    out = next_freeze_time(now)
    assert out == datetime(2026, 4, 27, 14, tzinfo=ET)


def test_next_freeze_at_cutoff_advances() -> None:
    # Boundary: exactly 14:00 ET advances to the next freeze day.
    # Matches perl `>= freeze_hour_policy`.
    now = datetime(2026, 4, 27, 14, 0, 0, tzinfo=ET)
    out = next_freeze_time(now)
    assert out == datetime(2026, 4, 28, 14, tzinfo=ET)


def test_next_freeze_skips_weekend() -> None:
    # Fri 2026-05-01 15:00 ET → after cutoff → next freeze is Mon 2026-05-04.
    now = datetime(2026, 5, 1, 15, tzinfo=ET)
    out = next_freeze_time(now)
    assert out == datetime(2026, 5, 4, 14, tzinfo=ET)


def test_next_freeze_skips_holiday() -> None:
    holidays = _make_lookup("2026-04-28")  # Tue holiday
    # Mon after cutoff → would land Tue, but Tue is holiday → Wed.
    now = datetime(2026, 4, 27, 15, tzinfo=ET)
    out = next_freeze_time(now, is_holiday=holidays)
    assert out == datetime(2026, 4, 29, 14, tzinfo=ET)


def test_next_freeze_accepts_utc_input() -> None:
    # 18:00 UTC == 14:00 EDT exact boundary → advances.
    now_utc = datetime(2026, 4, 27, 18, 0, 0, tzinfo=UTC)
    out = next_freeze_time(now_utc)
    assert out.astimezone(ET) == datetime(2026, 4, 28, 14, tzinfo=ET)


# next_publish_time ------------------------------------------------------------


def test_next_publish_before_cutoff_returns_today() -> None:
    # Mon 2026-04-27 19:59 ET — before 20:00 cutoff.
    now = datetime(2026, 4, 27, 19, 59, tzinfo=ET)
    out = next_publish_time(now)
    assert out == datetime(2026, 4, 27, 20, tzinfo=ET)


def test_next_publish_at_cutoff_advances() -> None:
    now = datetime(2026, 4, 27, 20, 0, tzinfo=ET)
    out = next_publish_time(now)
    assert out == datetime(2026, 4, 28, 20, tzinfo=ET)


def test_next_publish_friday_publishes_sunday() -> None:
    # Fri 2026-05-01 21:00 ET. After cutoff → skip Fri (already past),
    # but next_publish considers candidate Sat (not publish) and Sun
    # which IS a publish day when Friday wasn't a holiday.
    now = datetime(2026, 5, 1, 21, tzinfo=ET)
    out = next_publish_time(now)
    assert out == datetime(2026, 5, 3, 20, tzinfo=ET)


def test_next_publish_friday_holiday_publishes_monday() -> None:
    holidays = _make_lookup("2026-05-01")
    now = datetime(2026, 5, 1, 21, tzinfo=ET)
    out = next_publish_time(now, is_holiday=holidays)
    assert out == datetime(2026, 5, 4, 20, tzinfo=ET)


def test_next_publish_skips_multiday_holiday_stretch() -> None:
    # Christmas week 2026: Fri 12-25, Tue 12-29, Thu 12-31 (per seed).
    holidays = _make_lookup("2026-12-25", "2026-12-29", "2026-12-31")
    # Mon 2026-12-28 21:00 ET → after cutoff → look forward.
    # Tue 12-29 holiday → skip; Wed 12-30 is a publish day.
    now = datetime(2026, 12, 28, 21, tzinfo=ET)
    out = next_publish_time(now, is_holiday=holidays)
    assert out == datetime(2026, 12, 30, 20, tzinfo=ET)


# last_publish_time -------------------------------------------------------------


def test_last_publish_at_cutoff_returns_today() -> None:
    # Mon 2026-04-27 20:00 ET exactly — "at or after" includes the boundary.
    now = datetime(2026, 4, 27, 20, 0, tzinfo=ET)
    out = last_publish_time(now)
    assert out == datetime(2026, 4, 27, 20, tzinfo=ET)


def test_last_publish_after_cutoff_returns_today() -> None:
    now = datetime(2026, 4, 27, 21, tzinfo=ET)
    out = last_publish_time(now)
    assert out == datetime(2026, 4, 27, 20, tzinfo=ET)


def test_last_publish_before_cutoff_walks_back_to_sunday() -> None:
    # Mon 2026-04-27 10:00 ET — before today's cutoff, so walk back. Sunday
    # 2026-04-26 is a publish day (preceding Friday 4-24 not a holiday).
    now = datetime(2026, 4, 27, 10, tzinfo=ET)
    out = last_publish_time(now)
    assert out == datetime(2026, 4, 26, 20, tzinfo=ET)


def test_last_publish_skips_friday_saturday() -> None:
    # Fri 2026-05-01 10:00 ET — before cutoff, walk back. Thursday 4-30 is
    # the most recent publish day (Fri/Sat are never publish days).
    now = datetime(2026, 5, 1, 10, tzinfo=ET)
    out = last_publish_time(now)
    assert out == datetime(2026, 4, 30, 20, tzinfo=ET)


def test_last_publish_holiday_friday_skips_sunday_too() -> None:
    # Friday 4-24 was a holiday, so Sunday 4-26 is also not a publish day
    # (its own rule is "not is_holiday(preceding Friday)") -- must walk all
    # the way back to Thursday 4-23.
    holidays = _make_lookup("2026-04-24")
    now = datetime(2026, 4, 27, 10, tzinfo=ET)
    out = last_publish_time(now, is_holiday=holidays)
    assert out == datetime(2026, 4, 23, 20, tzinfo=ET)


# publish_time -------------------------------------------------------------------
# Reference table from Util.pm:50-58 (Freeze => Publish): Mon-Thu => same day,
# Fri => Sunday. A submission after today's freeze rolls to the *next* freeze
# day first, so its publish day shifts accordingly.


def test_publish_time_midweek_submission_same_day() -> None:
    # Mon 2026-04-27 10:00, before freeze -> today's freeze -> today's publish.
    now = datetime(2026, 4, 27, 10, tzinfo=ET)
    out = publish_time(now)
    assert out == datetime(2026, 4, 27, 20, tzinfo=ET)


def test_publish_time_friday_submission_publishes_sunday() -> None:
    # Fri 2026-05-01 10:00, before freeze -> Friday's freeze -> Sunday's publish.
    now = datetime(2026, 5, 1, 10, tzinfo=ET)
    out = publish_time(now)
    assert out == datetime(2026, 5, 3, 20, tzinfo=ET)


def test_publish_time_thursday_after_freeze_publishes_sunday() -> None:
    # Thu 2026-04-30 21:00, after Thursday's freeze -> next freeze is Friday
    # -> Friday's freeze publishes Sunday.
    now = datetime(2026, 4, 30, 21, tzinfo=ET)
    out = publish_time(now)
    assert out == datetime(2026, 5, 3, 20, tzinfo=ET)


def test_publish_time_saturday_submission_publishes_monday() -> None:
    # Sat 2026-05-02 10:00 -> no freeze on weekends -> next freeze is Monday
    # -> Monday's freeze publishes Monday.
    now = datetime(2026, 5, 2, 10, tzinfo=ET)
    out = publish_time(now)
    assert out == datetime(2026, 5, 4, 20, tzinfo=ET)


def test_publish_time_holiday_aware() -> None:
    holidays = _make_lookup("2026-05-01")  # Fri holiday
    # Thu 2026-04-30 21:00, after Thursday's freeze -> next freeze skips the
    # holiday Friday -> lands on Monday -> Monday's freeze publishes Monday.
    now = datetime(2026, 4, 30, 21, tzinfo=ET)
    out = publish_time(now, is_holiday=holidays)
    assert out == datetime(2026, 5, 4, 20, tzinfo=ET)


# is_between_freeze_and_publish ---------------------------------------------------


def test_is_between_true_at_exact_freeze_moment() -> None:
    now = datetime(2026, 4, 27, 14, 0, tzinfo=ET)  # Mon, exactly freeze
    assert is_between_freeze_and_publish(now) is True


def test_is_between_false_before_freeze() -> None:
    # Fri 2026-05-01 13:59, Friday's own freeze hasn't happened yet -- the
    # last freeze was Thursday, whose publish (Thu 20:00) already passed.
    now = datetime(2026, 5, 1, 13, 59, tzinfo=ET)
    assert is_between_freeze_and_publish(now) is False


def test_is_between_true_over_weekend_after_friday_freeze() -> None:
    # Fri's freeze publishes Sunday, so Saturday sits inside the window.
    now = datetime(2026, 5, 2, 10, 0, tzinfo=ET)
    assert is_between_freeze_and_publish(now) is True


def test_is_between_false_just_after_publish_buffer() -> None:
    # Sunday's publish is 20:00; the 1-minute race buffer closes at 20:01.
    now = datetime(2026, 5, 3, 20, 2, tzinfo=ET)
    assert is_between_freeze_and_publish(now) is False


def test_is_between_holiday_aware_diverges_from_default() -> None:
    # With Friday a holiday, Friday's freeze never happens: the last real
    # freeze was Thursday, and Thursday's publish (20:00 + buffer) is long
    # past by Saturday morning -- so the holiday-aware answer is False even
    # though the default (holiday-blind) answer for the same instant is True.
    holidays = _make_lookup("2026-05-01")
    now = datetime(2026, 5, 2, 10, 0, tzinfo=ET)
    assert is_between_freeze_and_publish(now) is True
    assert is_between_freeze_and_publish(now, is_holiday=holidays) is False
