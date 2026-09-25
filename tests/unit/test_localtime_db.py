"""Unit tests for :mod:`arxiv.submission.localtime_db`.

The database-backed half: loading the holiday calendar out of
``arXiv_holidays``, and the ``LocalTimeInfo`` aggregate the localtime page
renders on top of it. The pure calendar arithmetic these build on is covered
in ``test_arxiv_localtime.py``.

As there, "now" is always injected -- :func:`compute_localtime` takes a
``now`` argument precisely so the tests never read the real wall clock.

The holiday calendar comes from :data:`tests.conftest.HOLIDAY_DATES` (seeded
into the ``holidays`` / ``seeded_session`` fixtures):

    2025-01-01 Wed, 2025-01-20 Mon, 2025-07-04 Fri, 2025-11-27 Thu, 2025-12-25 Thu
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from arxiv.submission import localtime_db as lt

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
