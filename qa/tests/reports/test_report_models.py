"""Unit tests for QA report models."""

from pydantic import ValidationError
from unittest import TestCase

from qa.reports.models.base import BaseReport, Flag
from qa.reports.models.fulltext import FulltextReport


def base_report(
    name: str = "Test Report",
    key_name: str = "test-report",
    version: str = "1.0",
    submission_id: int = 1,
    data: dict = {},  # noqa: B006
) -> BaseReport:
    return BaseReport(
        name=name,
        key_name=key_name,
        version=version,
        submission_id=submission_id,
        data=data,
    )


class TestBaseReport(TestCase):
    def test_created_is_utc(self):
        self.assertRegex(base_report().created, r"\+00:00$")

    def test_key_name_rejects_underscores(self):
        with self.assertRaises(ValidationError):
            base_report(key_name="bad_key")

    def test_key_name_rejects_trailing_hyphen(self):
        with self.assertRaises(ValidationError):
            base_report(key_name="bad-")

    def test_submission_id_must_be_positive(self):
        with self.assertRaises(ValidationError):
            base_report(submission_id=0)


class TestFlag(TestCase):
    def test_id_rejects_underscores(self):
        with self.assertRaises(ValidationError):
            Flag(id="bad_flag", description=None)

    def test_id_accepts_kebab(self):
        Flag(id="tex-created-flag", description="a flag")


class TestFulltextReport(TestCase):
    def test_defaults(self):
        r = FulltextReport(submission_id=1, data={})
        self.assertEqual(r.name, "arXiv Fulltext Report")
        self.assertEqual(r.key_name, "fulltext")
        self.assertEqual(r.version, "1.0")

    def test_version_is_pinned(self):
        with self.assertRaises(ValidationError):
            FulltextReport(submission_id=1, data={}, version="2.0")  # type: ignore
