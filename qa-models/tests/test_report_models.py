"""Unit tests for QA report models."""

from pydantic import ValidationError
from unittest import TestCase

from qa_models.reports import AuthorCheckReport, Report, SummaryReport, Flag


class TestReportModels(TestCase):
    def test_report(self):

        AuthorCheckReport(
            qa_exec_time_sec=3,
            submission_id=1,
            version="1.0",
            data={"authors": ["au1", "au2"]},
        )

        foo_report = Report(
            name="Test Report",
            key_name="asdf",
            qa_exec_time_sec=3,
            submission_id=1,
            version="1.0",
            data={"bar": "baz"},
        )
        self.assertRegex(foo_report.created, r"\+00:00$")

        bar_report = Report(
            name="Test Report",
            key_name="test-report",
            qa_exec_time_sec=3,
            submission_id=1,
            version="1.0",
            created="2022-01-25T02:17:14.256300+00:00",
            data={"bar": "baz"},
        )
        self.assertEqual(
            bar_report,
            Report.model_validate_json(
                '{"name": "Test Report", "key_name": "test-report", "version": "1.0", "submission_id": 1, "created": "2022-01-25T02:17:14.256300+00:00", "flags": [], "qa_exec_time_sec": 3, "data": {"bar": "baz"}}'
            ),
        )

        with self.assertRaises(ValidationError):
            Report(
                name="Test Report Bad Key Name",
                key_name="test_",
                submission_id=1,
                version="1.0",
                data={"bar": "baz"},
            )

    def test_summary_report(self):

        foo_report = Report(
            name="Test Report",
            key_name="test",
            qa_exec_time_sec=3,
            submission_id=1,
            version="1.0",
            data={"bar": "baz"},
            flags=[Flag(id="missing-snozzberries", description="less than 50 percent found")],
        )

        SummaryReport(
            submission_id=1,
            reports=[foo_report],
            flagged_keys=["test"],
        )
