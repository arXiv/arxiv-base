"""Unit tests for QA report models."""

from pydantic import ValidationError
from unittest import TestCase

from qa.checks.models import BaseReport, Disposition, Flag, Result, SubmitEventInfo


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


class TestResultMessages(TestCase):
    def test_no_results_returns_empty_string(self):
        result = Result(check_config={}, passed=False, disposition=Disposition.REJECT, message="own message")
        self.assertEqual(result._messages(Disposition.REJECT), "")

    def test_concatenates_multiple_messages_at_the_same_disposition(self):
        result = Result(
            check_config={},
            passed=False,
            disposition=Disposition.REJECT,
            message="",
            results=[
                Result(check_config={}, passed=False, disposition=Disposition.REJECT, message="first reject message"),
                Result(check_config={}, passed=False, disposition=Disposition.REJECT, message="second reject message"),
            ],
        )
        self.assertEqual(result._messages(Disposition.REJECT), "first reject message\nsecond reject message")

    def test_filters_to_a_single_disposition(self):
        result = Result(
            check_config={},
            passed=False,
            disposition=Disposition.REJECT,
            message="",
            results=[
                Result(check_config={}, passed=False, disposition=Disposition.WARN, message="warn message"),
                Result(check_config={}, passed=False, disposition=Disposition.REJECT, message="reject message"),
            ],
        )
        self.assertEqual(result._messages(Disposition.REJECT), "reject message")

    def test_excludes_non_matching_dispositions(self):
        result = Result(
            check_config={},
            passed=True,
            disposition=Disposition.OK,
            message="",
            results=[
                Result(check_config={}, passed=True, disposition=Disposition.OK, message="passed message"),
                Result(check_config={}, passed=False, disposition=Disposition.OK, message="ignored message"),
                Result(check_config={}, passed=False, disposition=Disposition.WARN, message="warn message"),
            ],
        )
        self.assertEqual(result._messages(Disposition.WARN), "warn message")

    def test_includes_passed_sub_checks_with_matching_disposition(self):
        result = Result(
            check_config={},
            passed=True,
            disposition=Disposition.OK,
            message="",
            results=[
                Result(check_config={}, passed=True, disposition=Disposition.OK, message="passed message"),
                Result(check_config={}, passed=False, disposition=Disposition.OK, message="ignored message"),
            ],
        )
        self.assertEqual(result._messages(Disposition.OK), "passed message\nignored message")


class TestSubmitEventInfo(TestCase):
    def test_accepts_explicit_none_for_nullable_fields(self):
        info = SubmitEventInfo(type=None, is_oversize=None, submitter_name=None, source_format=None)
        self.assertIsNone(info.type)
        self.assertIsNone(info.is_oversize)
        self.assertIsNone(info.submitter_name)
        self.assertIsNone(info.source_format)

    def test_requires_type_field(self):
        with self.assertRaises(ValidationError):
            SubmitEventInfo.model_validate({"is_oversize": None, "submitter_name": None, "source_format": None})

    def test_requires_is_oversize_field(self):
        with self.assertRaises(ValidationError):
            SubmitEventInfo.model_validate({"type": None, "submitter_name": None, "source_format": None})

    def test_requires_submitter_name_field(self):
        with self.assertRaises(ValidationError):
            SubmitEventInfo.model_validate({"type": None, "is_oversize": None, "source_format": None})

    def test_requires_source_format_field(self):
        with self.assertRaises(ValidationError):
            SubmitEventInfo.model_validate({"type": None, "is_oversize": None, "submitter_name": None})


class TestFlag(TestCase):
    def test_id_rejects_underscores(self):
        with self.assertRaises(ValidationError):
            Flag(id="bad_flag", description=None)

    def test_id_accepts_kebab(self):
        Flag(id="tex-created-flag", description="a flag")
