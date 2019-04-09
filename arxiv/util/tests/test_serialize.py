"""Tests for :mod:`.serialize`."""

from unittest import TestCase, mock
from datetime import datetime, date
from pytz import UTC, timezone
from .. import serialize

ET = timezone('US/Eastern')


class TestISO8601JSONEncoder(TestCase):
    """
    Tests :func:`.serialize.dumps` and :class:`.serialize.ISO8601JSONEncoder`.
    """

    def test_encode_with_date(self):
        """Encode JSON with a :class:`.date` object."""
        self.assertEqual(
            serialize.dumps(date(year=1993, month=11, day=3)),
            '"1993-11-03"'
        )
        self.assertEqual(
            serialize.dumps({"date": date(year=1993, month=11, day=3)}),
            '{"date": "1993-11-03"}'
        )
        self.assertEqual(
            serialize.dumps([{"date": date(year=1993, month=11, day=3)}]),
            '[{"date": "1993-11-03"}]'
        )
        self.assertEqual(
            serialize.dumps([{"date": [date(year=1993, month=11, day=3)]}]),
            '[{"date": ["1993-11-03"]}]'
        )

    def test_encode_with_datetime(self):
        """Encode JSON with a :class:`.datetime` object."""
        self.assertEqual(
            serialize.dumps(datetime(year=1993, month=11, day=3)),
            '"1993-11-03T00:00:00"'
        )
        self.assertEqual(
            serialize.dumps({"date": datetime(year=1993, month=11, day=3)}),
            '{"date": "1993-11-03T00:00:00"}'
        )
        self.assertEqual(
            serialize.dumps([{"date": datetime(year=1993, month=11, day=3)}]),
            '[{"date": "1993-11-03T00:00:00"}]'
        )
        self.assertEqual(
            serialize.dumps([{"date": [datetime(year=1993, month=11, day=3)]}]),
            '[{"date": ["1993-11-03T00:00:00"]}]'
        )

    def test_encode_with_datetime_tz(self):
        """Encode JSON with a TZ-aware :class:`.datetime` object."""
        self.assertEqual(
            serialize.dumps(datetime(year=1993, month=11, day=3, tzinfo=ET)),
            '"1993-11-03T00:00:00-04:56"'
        )
        self.assertEqual(
            serialize.dumps({
                "date": datetime(year=1993, month=11, day=3, tzinfo=ET)
            }),
            '{"date": "1993-11-03T00:00:00-04:56"}'
        )
        self.assertEqual(
            serialize.dumps([
                {"date": datetime(year=1993, month=11, day=3, tzinfo=ET)}
            ]),
            '[{"date": "1993-11-03T00:00:00-04:56"}]'
        )
        self.assertEqual(
            serialize.dumps([
                {"date": [datetime(year=1993, month=11, day=3, tzinfo=ET)]}
            ]),
            '[{"date": ["1993-11-03T00:00:00-04:56"]}]'
        )


class TestISO8601JSONDecoder(TestCase):
    """
    Tests :func:`.serialize.loads` and :class:`.serialize.ISO8601JSONDecoder`.
    """

    def test_decode_with_date(self):
        """Decode JSON with a date value."""
        self.assertEqual(
            {"date": datetime(year=1993, month=11, day=3)},
            serialize.loads('{"date": "1993-11-03"}')
        )
        self.assertEqual(
            [{"date": datetime(year=1993, month=11, day=3)}],
            serialize.loads('[{"date": "1993-11-03"}]')
        )
        self.assertEqual(
            [{"date": [datetime(year=1993, month=11, day=3)]}],
            serialize.loads('[{"date": ["1993-11-03"]}]')
        )
        self.assertEqual(
            [{"date": ["1993"]}],
            serialize.loads('[{"date": ["1993"]}]')
        )

    def test_decode_with_datetime(self):
        """Decode JSON with a datetime value."""
        self.assertEqual(
            {"date": datetime(year=1993, month=11, day=3)},
            serialize.loads('{"date": "1993-11-03T00:00:00"}')
        )
        self.assertEqual(
            [{"date": datetime(year=1993, month=11, day=3)}],
            serialize.loads('[{"date": "1993-11-03T00:00:00"}]')
        )
        self.assertEqual(
            [{"date": [datetime(year=1993, month=11, day=3)]}],
            serialize.loads('[{"date": ["1993-11-03T00:00:00"]}]')
        )

    def test_encode_with_datetime_tz(self):
        """Decode JSON with a datetime value."""
        self.assertEqual(
            {"date": datetime(year=1993, month=11, day=3, tzinfo=ET)},
            serialize.loads('{"date": "1993-11-03T00:00:00-04:56"}')
        )
        self.assertEqual(
            [{"date": datetime(year=1993, month=11, day=3, tzinfo=ET)}],
            serialize.loads('[{"date": "1993-11-03T00:00:00-04:56"}]')
        )
        self.assertEqual(
            [{"date": [datetime(year=1993, month=11, day=3, tzinfo=ET)]}],
            serialize.loads('[{"date": ["1993-11-03T00:00:00-04:56"]}]')
        )
