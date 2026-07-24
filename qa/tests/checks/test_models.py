"""Unit tests for QA report models."""

from pydantic import ValidationError
from unittest import TestCase

from qa.checks.models import BaseReport, Disposition, Flag, Result


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


class TestResultFailureMessages(TestCase):
    def test_no_results_and_passed_returns_empty_string(self):
        result = Result(check_config={}, passed=True, disposition=Disposition.OK, message="")
        self.assertEqual(result.failure_messages(Disposition.WARN, Disposition.REJECT), "")

    def test_no_results_and_failed_returns_own_message(self):
        result = Result(check_config={}, passed=False, disposition=Disposition.REJECT, message="own message")
        self.assertEqual(result.failure_messages(Disposition.WARN, Disposition.REJECT), "own message")

    def test_no_dispositions_returns_empty_string(self):
        result = Result(
            check_config={},
            passed=False,
            disposition=Disposition.REJECT,
            message="",
            results=[
                Result(check_config={}, passed=False, disposition=Disposition.REJECT, message="reject message"),
            ],
        )
        self.assertEqual(result.failure_messages(), "")

    def test_concatenates_messages_matching_given_dispositions(self):
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
        self.assertEqual(
            result.failure_messages(Disposition.WARN, Disposition.REJECT), "warn message\nreject message"
        )

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
        self.assertEqual(result.failure_messages(Disposition.REJECT), "reject message")

    def test_excludes_passed_and_ignored_sub_checks(self):
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
        self.assertEqual(result.failure_messages(Disposition.WARN, Disposition.REJECT), "warn message")

    def test_excludes_passed_sub_checks_even_with_matching_disposition(self):
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
        self.assertEqual(result.failure_messages(Disposition.OK), "ignored message")


class TestFlag(TestCase):
    def test_id_rejects_underscores(self):
        with self.assertRaises(ValidationError):
            Flag(id="bad_flag", description=None)

    def test_id_accepts_kebab(self):
        Flag(id="tex-created-flag", description="a flag")
