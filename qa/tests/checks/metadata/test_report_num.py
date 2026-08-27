"""Tests for ReportNumIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry, Result
from qa.checks.metadata.report_num import ReportNumIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestReportNumIsValid:
    def test_pass_normal(self):
        assert ReportNumIsValid.check("CERN-EP-2024-001").passed

    def test_pass_none(self):
        result = ReportNumIsValid.check(None)
        assert result.passed
        assert result.results == []

    def test_pass_empty(self):
        result = ReportNumIsValid.check("")
        assert result.passed
        assert result.results == []

    def test_warn_too_short(self):
        result = ReportNumIsValid.check("A1")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_too_short_two_chars(self):
        result = ReportNumIsValid.check("A2")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_too_short_three_chars(self):
        result = ReportNumIsValid.check("A23")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_fail_no_letters_four_digits(self):
        result = ReportNumIsValid.check("1234")
        assert not result.passed
        assert not sub_result(result, "contains_a_letter_and_a_digit").passed

    def test_fail_no_letters_five_digits(self):
        result = ReportNumIsValid.check("12345")
        assert not result.passed
        assert not sub_result(result, "contains_a_letter_and_a_digit").passed

    def test_pass_multiple_report_nums(self):
        assert ReportNumIsValid.check("ECTP-2024-05; WLCAPP-2024-05; FUE-2024-05").passed

    def test_warn_too_long(self):
        result = ReportNumIsValid.check("X" * 2000 + "1")
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_warn_contains_url(self):
        result = ReportNumIsValid.check("https://example.com/report2024")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_http_url(self):
        result = ReportNumIsValid.check("http://example.com/report2024")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi(self):
        result = ReportNumIsValid.check("doi:10.1234/abc123")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_fail_no_letters(self):
        result = ReportNumIsValid.check("1234567")
        assert not result.passed
        assert not sub_result(result, "contains_a_letter_and_a_digit").passed

    def test_fail_no_digits(self):
        result = ReportNumIsValid.check("ABCDEFG")
        assert not result.passed
        assert not sub_result(result, "contains_a_letter_and_a_digit").passed

    def test_pass_extra_whitespace_without_cleanup(self):
        """Extra whitespace is only normalized via cleanup(); check() no longer rejects it directly."""
        assert ReportNumIsValid.check("CERN  EP-2024-001").passed

    def test_pass_space_in_parens_without_cleanup(self):
        """Unnecessary space in parens is only normalized via cleanup(); check() no longer rejects it directly."""
        assert ReportNumIsValid.check("CERN-EP-2024-001 ( draft )").passed

    def test_pass_control_chars_without_cleanup(self):
        """Control characters are only normalized via cleanup(); check() no longer rejects them directly."""
        assert ReportNumIsValid.check("CERN-EP\t2024-001").passed

    def test_fail_malformed_unicode(self):
        result = ReportNumIsValid.check("CERN \xc0\x80 2024-001")
        assert not result.passed
        assert not sub_result(result, "no_utf8_decoding_errors").passed

    def test_all_sub_checks_run_on_valid(self):
        result = ReportNumIsValid.check("CERN-EP-2024-001")
        assert result.results is not None
        assert len(result.results) == len(ReportNumIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            ReportNumIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = ReportNumIsValid.check("CERN-EP-2024-001")
        assert result.check_config["name"] == "report_num_is_valid"
        assert result.check_config["id"] == 500
        assert result.check_config["version"] == "1.0.0"


class TestCleanup:
    def test_collapses_whitespace_strips_and_removes_trailing_period(self):
        assert ReportNumIsValid.cleanup("  CERN-EP-2024-001.  ") == "CERN-EP-2024-001"

    def test_removes_control_chars(self):
        assert ReportNumIsValid.cleanup("CERN-EP\t2024-001") == "CERN-EP 2024-001"

    def test_removes_space_before_comma(self):
        assert ReportNumIsValid.cleanup("CERN-EP-2024-001 , WLCAPP-2024-05") == "CERN-EP-2024-001, WLCAPP-2024-05"

    def test_removes_unnecessary_space_in_parens(self):
        assert ReportNumIsValid.cleanup("CERN-EP-2024-001 ( draft )") == "CERN-EP-2024-001 (draft)"
