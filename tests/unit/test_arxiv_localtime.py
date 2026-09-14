"""Unit tests for :mod:`arxiv.submission.arxiv_localtime`.

These tests encode the arXiv submission-timing *business rules*, not just the
current code. The workflow question they answer is: "If I submit a paper now,
when does it freeze, when is it announced, and when is the announcement after
that if I miss the deadline?"

Two things drive the design:

* **"now" is always injected.** None of the functions under test are allowed
  to be tested against the real wall clock -- results would drift day to day.
  Every test passes an explicit ``datetime``. :func:`compute_localtime` already
  accepts a ``now`` argument for exactly this reason, and the tests use it.

* **Boundaries are the point.** The interesting behaviour lives at the edges:
  the exact freeze second (14:00:00), the exact publish second (20:00:00), the
  Friday/Saturday/Sunday seam, holidays that abut weekends, and the EST/EDT
  daylight-saving change. Each edge gets a test that pins the *intended* answer.

The holiday calendar comes from :data:`tests.conftest.HOLIDAY_DATES` (seeded in
the ``holidays`` / ``seeded_session`` fixtures):

    2025-01-01 Wed, 2025-01-20 Mon, 2025-07-04 Fri, 2025-11-27 Thu, 2025-12-25 Thu
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from arxiv.submission import arxiv_localtime as lt

TZ = ZoneInfo("America/New_York")


def biz(year: int, month: int, day: int,
        hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """Build a business-tz (America/New_York) aware datetime."""
    return datetime(year, month, day, hour, minute, second, tzinfo=TZ)


# ==========================================================================
# get_holidays -- DB-backed calendar load
# ==========================================================================

class TestGetHolidays:
    """Loading the holiday calendar out of the ``arXiv_holidays`` table."""

    def test_loads_all_seeded_holidays(self, seeded_session: Session) -> None:
        """With no bounds, every seeded holiday comes back as an ISO string."""
        got = lt.get_holidays(seeded_session, start_date=None, end_date=None)
        assert got == frozenset({
            "2025-01-01", "2025-01-20", "2025-07-04",
            "2025-11-27", "2025-12-25",
        })

    def test_empty_table_is_empty_set(self, db_session: Session) -> None:
        """No rows -> empty set, not an error."""
        assert lt.get_holidays(db_session, start_date=None) == frozenset()

    def test_start_date_is_inclusive_lower_bound(self, seeded_session: Session) -> None:
        """``start_date`` filters out earlier holidays, keeps the equal one."""
        got = lt.get_holidays(seeded_session, start_date=date(2025, 1, 20))
        # 2025-01-01 dropped; 2025-01-20 kept (inclusive).
        assert "2025-01-01" not in got
        assert "2025-01-20" in got

    def test_end_date_is_inclusive_upper_bound(self, seeded_session: Session) -> None:
        """``end_date`` keeps the equal date and drops later ones."""
        got = lt.get_holidays(seeded_session,
                              start_date=None, end_date=date(2025, 7, 4))
        assert got == frozenset({"2025-01-01", "2025-01-20", "2025-07-04"})

    def test_callable_start_date_is_resolved(self, seeded_session: Session) -> None:
        """A zero-arg callable start bound is called (the default is date.today).

        Passing a callable is how the production default avoids baking in a
        real 'today'; here we prove the callable is invoked rather than used
        as a value.
        """
        got = lt.get_holidays(seeded_session,
                              start_date=lambda: date(2025, 7, 1))
        assert got == frozenset({"2025-07-04", "2025-11-27", "2025-12-25"})


# ==========================================================================
# Calendar predicates -- is_holiday / is_workday / is_publish_day
# ==========================================================================

class TestIsHoliday:
    def test_listed_date_is_holiday(self, holidays: frozenset[str]) -> None:
        assert lt.is_holiday(date(2025, 1, 1), holidays) is True

    def test_ordinary_weekday_is_not_holiday(self, holidays: frozenset[str]) -> None:
        assert lt.is_holiday(date(2025, 1, 7), holidays) is False

    def test_weekend_is_not_a_holiday(self, holidays: frozenset[str]) -> None:
        """Weekends are handled separately; they are not 'holidays' here."""
        assert lt.is_holiday(date(2025, 1, 11), holidays) is False  # Saturday


class TestIsWorkday:
    """A workday is a freeze day: a weekday that is not an arXiv holiday."""

    def test_ordinary_weekday_is_workday(self, holidays: frozenset[str]) -> None:
        assert lt.is_workday(date(2025, 1, 7), holidays) is True  # Tuesday

    def test_saturday_is_not_workday(self, holidays: frozenset[str]) -> None:
        assert lt.is_workday(date(2025, 1, 11), holidays) is False

    def test_sunday_is_not_workday(self, holidays: frozenset[str]) -> None:
        assert lt.is_workday(date(2025, 1, 12), holidays) is False

    def test_holiday_weekday_is_not_workday(self, holidays: frozenset[str]) -> None:
        assert lt.is_workday(date(2025, 1, 1), holidays) is False  # Wed holiday


class TestIsPublishDay:
    """Mailing/announcement runs. Port of ``isPublishDay``.

    - Fri & Sat: cron never runs -> never a publish day.
    - Sun: a publish day only if the *preceding Friday* was a workday.
    - Mon-Thu: a publish day unless the day itself is a holiday.
    """

    def test_weekday_is_publish_day(self, holidays: frozenset[str]) -> None:
        assert lt.is_publish_day(date(2025, 1, 7), holidays) is True  # Tue

    def test_friday_is_never_publish_day(self, holidays: frozenset[str]) -> None:
        assert lt.is_publish_day(date(2025, 1, 10), holidays) is False

    def test_saturday_is_never_publish_day(self, holidays: frozenset[str]) -> None:
        assert lt.is_publish_day(date(2025, 1, 11), holidays) is False

    def test_sunday_publishes_when_prior_friday_was_a_workday(self, holidays: frozenset[str]) -> None:
        """Sun 2025-01-12: the preceding Fri (01-10) was a normal workday."""
        assert lt.is_publish_day(date(2025, 1, 12), holidays) is True

    def test_sunday_does_not_publish_when_prior_friday_was_a_holiday(self, holidays: frozenset[str]) -> None:
        """Sun 2025-07-06: preceding Fri (07-04) is a holiday -> no publish.

        This is the whole reason Friday holidays are special: the Sunday
        mailing rides on Friday's freeze, so if Friday froze nothing there is
        nothing to mail on Sunday.
        """
        assert lt.is_publish_day(date(2025, 7, 6), holidays) is False

    def test_holiday_weekday_is_not_publish_day(self, holidays: frozenset[str]) -> None:
        assert lt.is_publish_day(date(2025, 1, 1), holidays) is False


# ==========================================================================
# Policy hours -- freeze_hour_policy / publish_hour_policy
# ==========================================================================

class TestFreezeHourPolicy:
    """Freeze was 16:00 through 2017-01-01, then 14:00 from 2017-01-02 on."""

    def test_before_2017_is_16(self, holidays: frozenset[str]) -> None:
        assert lt.freeze_hour_policy(biz(2016, 6, 1)) == 16

    def test_exactly_2017_01_01_is_still_16(self, holidays: frozenset[str]) -> None:
        """The policy-change boundary: the last 16:00 day is 2017-01-01."""
        assert lt.freeze_hour_policy(biz(2017, 1, 1, 23, 59, 59)) == 16

    def test_2017_01_02_flips_to_14(self, holidays: frozenset[str]) -> None:
        """First 14:00 day is 2017-01-02, from its very first second."""
        assert lt.freeze_hour_policy(biz(2017, 1, 2, 0, 0, 0)) == 14

    def test_modern_dates_are_14(self, holidays: frozenset[str]) -> None:
        assert lt.freeze_hour_policy(biz(2025, 1, 7)) == 14


def test_publish_hour_policy_is_20() -> None:
    assert lt.publish_hour_policy() == 20


# ==========================================================================
# Workday walking -- next_workday / last_workday
# ==========================================================================

class TestWorkdayWalking:
    def test_next_workday_on_a_workday_is_unchanged(self, holidays: frozenset[str]) -> None:
        start = biz(2025, 1, 7, 9, 30)  # Tuesday
        assert lt.next_workday(start, holidays) == start

    def test_friday_is_a_workday(self, holidays: frozenset[str]) -> None:
        """Freeze runs Mon-Fri; Friday is a workday even though it never mails."""
        start = biz(2025, 1, 10, 9, 30)  # Friday
        assert lt.next_workday(start, holidays) == start

    def test_next_workday_preserves_time_of_day(self, holidays: frozenset[str]) -> None:
        """Stepping over a weekend keeps the clock time; only the date moves."""
        # Saturday -> skips Sat/Sun -> Monday, still 09:30.
        result = lt.next_workday(biz(2025, 1, 11, 9, 30), holidays)
        assert result == biz(2025, 1, 13, 9, 30)

    def test_next_workday_skips_weekend_and_monday_holiday(self, holidays: frozenset[str]) -> None:
        """Sat -> Sun -> Mon(MLK holiday) -> Tue 2025-01-21."""
        result = lt.next_workday(biz(2025, 1, 18, 8, 0), holidays)
        assert result == biz(2025, 1, 21, 8, 0)

    def test_last_workday_steps_back_over_weekend(self, holidays: frozenset[str]) -> None:
        """Sunday steps back to Friday, preserving time."""
        result = lt.last_workday(biz(2025, 1, 12, 9, 30), holidays)
        assert result == biz(2025, 1, 10, 9, 30)

    def test_last_workday_skips_back_over_holiday(self, holidays: frozenset[str]) -> None:
        """Mon 2025-01-20 is MLK holiday -> step back to Fri 2025-01-17."""
        result = lt.last_workday(biz(2025, 1, 20, 9, 30), holidays)
        assert result == biz(2025, 1, 17, 9, 30)


# ==========================================================================
# next_freeze_time -- the submission deadline
# ==========================================================================

class TestNextFreezeTime:
    """Next freeze at/after a submission time. Freeze hour is 14:00.

    The critical boundary is the freeze second itself: submitting *at* 14:00
    means the deadline has passed, so the next freeze is the next workday.
    """

    def test_before_freeze_hour_freezes_today(self, holidays: frozenset[str]) -> None:
        result = lt.next_freeze_time(biz(2025, 1, 7, 9, 0), holidays)
        assert result == biz(2025, 1, 7, 14, 0)

    def test_one_second_before_freeze_still_freezes_today(self, holidays: frozenset[str]) -> None:
        """13:59:59 -> today's 14:00. The deadline has not yet passed."""
        result = lt.next_freeze_time(biz(2025, 1, 7, 13, 59, 59), holidays)
        assert result == biz(2025, 1, 7, 14, 0)

    def test_exactly_at_freeze_hour_rolls_to_next_workday(self, holidays: frozenset[str]) -> None:
        """14:00:00 exactly -> the deadline passed -> tomorrow's freeze.

        This is the key deadline semantic: hitting 14:00 on the dot misses
        today's freeze.
        """
        result = lt.next_freeze_time(biz(2025, 1, 7, 14, 0, 0), holidays)
        assert result == biz(2025, 1, 8, 14, 0)

    def test_friday_after_freeze_rolls_to_monday(self, holidays: frozenset[str]) -> None:
        """Fri 15:00 -> Sat/Sun skipped -> Mon 2025-01-13 14:00."""
        result = lt.next_freeze_time(biz(2025, 1, 10, 15, 0), holidays)
        assert result == biz(2025, 1, 13, 14, 0)

    def test_friday_before_freeze_freezes_friday(self, holidays: frozenset[str]) -> None:
        result = lt.next_freeze_time(biz(2025, 1, 10, 13, 0), holidays)
        assert result == biz(2025, 1, 10, 14, 0)

    def test_rolls_over_weekend_into_monday_holiday(self, holidays: frozenset[str]) -> None:
        """Fri 2025-01-17 15:00 -> Sat/Sun/Mon(MLK) skipped -> Tue 01-21 14:00."""
        result = lt.next_freeze_time(biz(2025, 1, 17, 15, 0), holidays)
        assert result == biz(2025, 1, 21, 14, 0)

    def test_naive_and_aware_inputs_agree(self, holidays: frozenset[str]) -> None:
        """Aware input is converted to business tz; a UTC-equivalent matches."""
        aware_utc = datetime(2025, 1, 7, 14, 0, tzinfo=ZoneInfo("UTC"))
        # 14:00 UTC == 09:00 EST -> still before the 14:00 EST freeze.
        result = lt.next_freeze_time(aware_utc, holidays)
        assert result == biz(2025, 1, 7, 14, 0)


# ==========================================================================
# last_freeze_time -- most recent freeze at/before a moment
# ==========================================================================

class TestLastFreezeTime:
    def test_before_freeze_hour_uses_previous_workday(self, holidays: frozenset[str]) -> None:
        """13:00 Tue -> last freeze was Mon 2025-01-06 14:00."""
        result = lt.last_freeze_time(biz(2025, 1, 7, 13, 0), holidays)
        assert result == biz(2025, 1, 6, 14, 0)

    def test_exactly_at_freeze_hour_returns_today(self, holidays: frozenset[str]) -> None:
        """At 14:00 exactly, the freeze *is* today's -- not yesterday's.

        :func:`is_between_freeze_and_publish` relies on this inclusive edge.
        """
        result = lt.last_freeze_time(biz(2025, 1, 7, 14, 0), holidays)
        assert result == biz(2025, 1, 7, 14, 0)

    def test_after_freeze_hour_returns_today(self, holidays: frozenset[str]) -> None:
        result = lt.last_freeze_time(biz(2025, 1, 7, 15, 0), holidays)
        assert result == biz(2025, 1, 7, 14, 0)

    def test_monday_before_freeze_steps_back_over_weekend(self, holidays: frozenset[str]) -> None:
        """Mon 2025-01-13 09:00 -> last freeze Fri 2025-01-10 14:00."""
        result = lt.last_freeze_time(biz(2025, 1, 13, 9, 0), holidays)
        assert result == biz(2025, 1, 10, 14, 0)


# ==========================================================================
# next_publish_time -- the next scheduled mailing
# ==========================================================================

class TestNextPublishTime:
    """Next mailing from a moment. Publish hour is 20:00.

    Like the freeze edge, hitting 20:00 exactly means today's mailing has
    gone -> roll to the next publish day.
    """

    def test_before_publish_hour_publishes_today(self, holidays: frozenset[str]) -> None:
        result = lt.next_publish_time(biz(2025, 1, 7, 19, 0), holidays)
        assert result == biz(2025, 1, 7, 20, 0)

    def test_exactly_at_publish_hour_rolls_forward(self, holidays: frozenset[str]) -> None:
        """20:00:00 -> today's mailing already ran -> next publish day."""
        result = lt.next_publish_time(biz(2025, 1, 7, 20, 0), holidays)
        assert result == biz(2025, 1, 8, 20, 0)

    def test_friday_evening_skips_to_sunday(self, holidays: frozenset[str]) -> None:
        """Fri after publish: Sat never publishes, Sun does (Fri was a workday).

        Fri 2025-01-10 21:00 -> Sat skipped -> Sun 2025-01-12 20:00.
        """
        result = lt.next_publish_time(biz(2025, 1, 10, 21, 0), holidays)
        assert result == biz(2025, 1, 12, 20, 0)

    def test_friday_holiday_skips_sunday_to_monday(self, holidays: frozenset[str]) -> None:
        """With Fri 07-04 a holiday, Sun 07-06 does not publish -> Mon 07-07.

        Thu 2025-07-03 21:00 -> Fri(holiday)/Sat/Sun all skipped -> Mon 20:00.
        """
        result = lt.next_publish_time(biz(2025, 7, 3, 21, 0), holidays)
        assert result == biz(2025, 7, 7, 20, 0)


# ==========================================================================
# publish_time -- when a paper submitted at ``now`` gets announced
# ==========================================================================

class TestPublishTime:
    """End-to-end: submission time -> its freeze -> the mailing after it."""

    def test_morning_submission_publishes_same_evening(self, holidays: frozenset[str]) -> None:
        """Submit Tue 09:00 -> freeze Tue 14:00 -> mail Tue 20:00."""
        result = lt.publish_time(biz(2025, 1, 7, 9, 0), holidays)
        assert result == biz(2025, 1, 7, 20, 0)

    def test_submission_after_freeze_publishes_next_day(self, holidays: frozenset[str]) -> None:
        """Submit Tue 15:00 (deadline missed) -> freeze Wed 14:00 -> Wed 20:00."""
        result = lt.publish_time(biz(2025, 1, 7, 15, 0), holidays)
        assert result == biz(2025, 1, 8, 20, 0)

    def test_submission_before_friday_holiday_weekend(self, holidays: frozenset[str]) -> None:
        """Thu 07-03 after freeze -> next freeze Mon 07-07 -> mail Mon 20:00.

        Fri 07-04 holiday plus the weekend push both freeze and mailing to
        Monday.
        """
        result = lt.publish_time(biz(2025, 7, 3, 15, 0), holidays)
        assert result == biz(2025, 7, 7, 20, 0)


# ==========================================================================
# is_between_freeze_and_publish
# ==========================================================================

class TestIsBetweenFreezeAndPublish:
    """True while ``now`` sits in the freeze->publish window (14:00..20:00).

    The window is inclusive at the freeze edge and carries a one-minute
    cushion past publish to avoid races.
    """

    def test_just_before_freeze_is_false(self, holidays: frozenset[str]) -> None:
        assert lt.is_between_freeze_and_publish(
            biz(2025, 1, 7, 13, 0), holidays) is False

    def test_exactly_at_freeze_is_true(self, holidays: frozenset[str]) -> None:
        """14:00 exactly is inside the window (inclusive lower edge)."""
        assert lt.is_between_freeze_and_publish(
            biz(2025, 1, 7, 14, 0), holidays) is True

    def test_mid_window_is_true(self, holidays: frozenset[str]) -> None:
        assert lt.is_between_freeze_and_publish(
            biz(2025, 1, 7, 15, 0), holidays) is True

    def test_at_publish_is_true(self, holidays: frozenset[str]) -> None:
        assert lt.is_between_freeze_and_publish(
            biz(2025, 1, 7, 20, 0), holidays) is True

    def test_within_one_minute_cushion_is_true(self, holidays: frozenset[str]) -> None:
        """20:01 -> still true; the cushion guards the publish edge."""
        assert lt.is_between_freeze_and_publish(
            biz(2025, 1, 7, 20, 1), holidays) is True

    def test_past_cushion_is_false(self, holidays: frozenset[str]) -> None:
        """20:02 -> past the one-minute cushion -> outside the window."""
        assert lt.is_between_freeze_and_publish(
            biz(2025, 1, 7, 20, 2), holidays) is False


# ==========================================================================
# compute_localtime -- the aggregate the localtime page consumes
# ==========================================================================

class TestComputeLocaltime:
    """The full bundle. ``now`` is injected so results are deterministic."""

    def test_now_is_required_to_be_deterministic(self, seeded_session: Session) -> None:
        """Passing ``now`` explicitly is what makes these assertions stable.

        (The default path calls ``datetime.now`` -- untestable by value -- so
        every assertion here supplies its own reference time.)
        """
        info = lt.compute_localtime(seeded_session, now=biz(2025, 1, 7, 9, 0))
        assert info.now == biz(2025, 1, 7, 9, 0)

    def test_typical_morning_submission(self, seeded_session: Session) -> None:
        """Tue 09:00: freeze 14:00 today, mailed 20:00 today, next mail Wed.

        This is the everyday case: submit in the morning, make the 14:00
        freeze, get mailed the same evening; missing it means the following
        evening.
        """
        info = lt.compute_localtime(seeded_session, now=biz(2025, 1, 7, 9, 0))
        assert info.next_freeze == biz(2025, 1, 7, 14, 0)
        assert info.duration_to_freeze == timedelta(hours=5)
        assert info.next_mail == biz(2025, 1, 7, 20, 0)
        assert info.subsequent_mail == biz(2025, 1, 8, 20, 0)
        assert info.publish_time_now == biz(2025, 1, 7, 20, 0)
        assert info.freeze_hour == 14

    def test_between_freeze_and_publish_reports_current_cycle_mailing(
            self, seeded_session: Session, holidays: frozenset[str]) -> None:
        """Tue 15:00 (after freeze, before mailing): publish_time_now is the
        mailing for the freeze that just happened, not the next one.

        Business intent: once you are inside the freeze->publish window the
        page must still show the mailing your just-frozen paper rides in --
        the previous cycle's 20:00 -- rather than jumping a day ahead.
        """
        info = lt.compute_localtime(seeded_session, now=biz(2025, 1, 7, 15, 0))
        # A naive publish_time() for a 15:00 submission would say Wed 20:00...
        assert lt.publish_time(biz(2025, 1, 7, 15, 0),
                               holidays) == biz(2025, 1, 8, 20, 0)
        # ...but the window adjustment reports today's 20:00 mailing.
        assert info.publish_time_now == biz(2025, 1, 7, 20, 0)

    def test_naive_now_is_treated_as_business_tz(self, seeded_session: Session) -> None:
        """A naive ``now`` is interpreted in business tz, not UTC."""
        info = lt.compute_localtime(seeded_session,
                                    now=datetime(2025, 1, 7, 9, 0))
        assert info.now == biz(2025, 1, 7, 9, 0)
        assert info.next_freeze == biz(2025, 1, 7, 14, 0)

    def test_aware_now_is_converted_to_business_tz(self, seeded_session: Session) -> None:
        """An aware ``now`` in another zone is converted, not rejected.

        14:00 UTC == 09:00 EST -> the morning case above.
        """
        info = lt.compute_localtime(
            seeded_session,
            now=datetime(2025, 1, 7, 14, 0, tzinfo=ZoneInfo("UTC")))
        assert info.now == biz(2025, 1, 7, 9, 0)
        assert info.next_freeze == biz(2025, 1, 7, 14, 0)

    def test_winter_reports_est(self, seeded_session: Session) -> None:
        info = lt.compute_localtime(seeded_session, now=biz(2025, 1, 7, 9, 0))
        assert info.arxiv_tz == "EST"

    def test_summer_reports_edt(self, seeded_session: Session) -> None:
        """Daylight-saving boundary: the same page reads EDT in July."""
        info = lt.compute_localtime(seeded_session, now=biz(2025, 7, 8, 9, 0))
        assert info.arxiv_tz == "EDT"

    def test_friday_holiday_weekend_pushes_everything_to_monday(
            self, seeded_session: Session) -> None:
        """Thu 2025-07-03 15:00: deadline missed, and Fri 07-04 is a holiday.

        Next freeze is Mon 07-07 (Fri holiday + weekend), and the mailing is
        Mon 07-07 20:00 -- the whole holiday weekend collapses forward.
        """
        info = lt.compute_localtime(seeded_session, now=biz(2025, 7, 3, 15, 0))
        assert info.next_freeze == biz(2025, 7, 7, 14, 0)
        assert info.next_mail == biz(2025, 7, 7, 20, 0)

    def test_matches_db_backed_and_frozenset_paths(self, seeded_session: Session, holidays: frozenset[str]) -> None:
        """The DB-seeded calendar and the fixture frozenset agree.

        Proves the ``seeded_session`` fixture and the ``holidays`` fixture
        describe the same calendar, so the pure-function tests and the
        DB-backed tests are testing one consistent world.
        """
        now = biz(2025, 1, 7, 9, 0)
        info = lt.compute_localtime(seeded_session, now=now)
        assert info.next_freeze == lt.next_freeze_time(now, holidays)
        assert info.next_mail == lt.next_publish_time(
            lt.next_freeze_time(now, holidays), holidays)


# ==========================================================================
# Daylight-saving boundary -- the EST <-> EDT change
# ==========================================================================

class TestDaylightSavingBoundary:
    """Behaviour across the actual DST transitions, not just Jan vs July.

    2025 US transitions (America/New_York):
      * spring forward: Sun 2025-03-09, 02:00 EST -> 03:00 EDT (an hour vanishes)
      * fall back:      Sun 2025-11-02, 02:00 EDT -> 01:00 EST (an hour repeats)

    Two things matter here:

    * the reported ``arxiv_tz`` label flips exactly at the transition; and
    * ``duration_to_freeze`` is a *wall-clock* difference. ``next_freeze`` and
      ``now`` share one ``ZoneInfo`` object, and Python subtracts same-tzinfo
      datetimes on their naive wall values -- offsets ignored. So the freeze is
      always pinned to 14:00 wall-clock and the countdown counts wall hours,
      which across a DST change is NOT the real elapsed time. These tests pin
      that intended wall-clock semantics.
    """

    def test_label_flips_est_to_edt_at_spring_forward(
            self, seeded_session: Session) -> None:
        """Same weekend, an hour apart across the seam: EST before, EDT after."""
        before = lt.compute_localtime(seeded_session, now=biz(2025, 3, 9, 1, 0))
        after = lt.compute_localtime(seeded_session, now=biz(2025, 3, 9, 3, 0))
        assert before.arxiv_tz == "EST"
        assert after.arxiv_tz == "EDT"

    def test_label_flips_edt_to_est_at_fall_back(
            self, seeded_session: Session) -> None:
        """Fall back: EDT just before 02:00, EST after."""
        before = lt.compute_localtime(seeded_session,
                                      now=biz(2025, 11, 2, 0, 30))
        after = lt.compute_localtime(seeded_session, now=biz(2025, 11, 2, 3, 0))
        assert before.arxiv_tz == "EDT"
        assert after.arxiv_tz == "EST"

    def test_freeze_pinned_to_wall_clock_1400_after_spring_forward(
            self, holidays: frozenset[str]) -> None:
        """A freeze on an EDT day is 14:00 EDT, regardless of the EST start.

        Submit Fri 2025-03-07 15:00 EST (after freeze) -> next freeze is Mon
        2025-03-10 14:00 *EDT*: the freeze tracks 14:00 local wall time, so it
        lands an hour earlier in real (UTC) terms than the naive EST reading.
        """
        result = lt.next_freeze_time(biz(2025, 3, 7, 15, 0), holidays)
        assert result == biz(2025, 3, 10, 14, 0)
        assert result.utcoffset() == timedelta(hours=-4)  # EDT

    def test_duration_is_wall_clock_across_spring_forward(
            self, seeded_session: Session) -> None:
        """Countdown is wall-clock: 71h shown though only 70h real elapse.

        now = Fri 2025-03-07 15:00 EST, next_freeze = Mon 2025-03-10 14:00 EDT.
        Wall-clock difference is 2d23h = 71h. The true elapsed time is 70h
        (spring-forward eats an hour), but the page counts wall-clock hours.
        """
        info = lt.compute_localtime(seeded_session, now=biz(2025, 3, 7, 15, 0))
        assert info.next_freeze == biz(2025, 3, 10, 14, 0)
        assert info.duration_to_freeze == timedelta(hours=71)
        # Real elapsed (via UTC) is an hour less -- documents the difference.
        real_elapsed = (info.next_freeze.astimezone(ZoneInfo("UTC"))
                        - info.now.astimezone(ZoneInfo("UTC")))
        assert real_elapsed == timedelta(hours=70)

    def test_duration_is_wall_clock_across_fall_back(
            self, seeded_session: Session) -> None:
        """Mirror case: 71h wall-clock shown though 72h real elapse.

        now = Fri 2025-10-31 15:00 EDT, next_freeze = Mon 2025-11-03 14:00 EST.
        Wall-clock difference is again 71h, but the repeated hour means 72h of
        real time actually pass.
        """
        info = lt.compute_localtime(seeded_session, now=biz(2025, 10, 31, 15, 0))
        assert info.next_freeze == biz(2025, 11, 3, 14, 0)
        assert info.duration_to_freeze == timedelta(hours=71)
        real_elapsed = (info.next_freeze.astimezone(ZoneInfo("UTC"))
                        - info.now.astimezone(ZoneInfo("UTC")))
        assert real_elapsed == timedelta(hours=72)


# ==========================================================================
# compute_localtime_cached -- minute cache, explicit-now bypass
# ==========================================================================

class TestComputeLocaltimeCached:
    """The cache must never let one ``now`` leak into another's result."""

    def test_explicit_now_bypasses_cache(self, seeded_session: Session) -> None:
        """Distinct explicit ``now`` values must yield distinct results.

        The cache only covers the live (``now is None``) path; an explicit
        ``now`` is deterministic and must bypass the cache, or two different
        timestamps could collide within one wall-clock minute.
        """
        first = lt.compute_localtime_cached(
            seeded_session, now=biz(2025, 1, 7, 9, 0))
        second = lt.compute_localtime_cached(
            seeded_session, now=biz(2025, 7, 3, 15, 0))
        assert first.next_freeze == biz(2025, 1, 7, 14, 0)
        assert second.next_freeze == biz(2025, 7, 7, 14, 0)
        assert first.arxiv_tz == "EST"
        assert second.arxiv_tz == "EDT"

    def test_explicit_now_matches_uncached(self, seeded_session: Session) -> None:
        now = biz(2025, 1, 7, 9, 0)
        cached = lt.compute_localtime_cached(seeded_session, now=now)
        uncached = lt.compute_localtime(seeded_session, now=now)
        assert cached == uncached
