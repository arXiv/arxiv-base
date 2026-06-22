"""Tests for ReportNumIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result
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
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_too_short_two_digits(self):
        result = ReportNumIsValid.check("12")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_too_short_three_digits(self):
        result = ReportNumIsValid.check("123")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_no_letters_four_digits(self):
        result = ReportNumIsValid.check("1234")
        assert result.passed
        assert not sub_result(result, "contains_letters").passed

    def test_warn_no_letters_five_digits(self):
        result = ReportNumIsValid.check("12345")
        assert result.passed
        assert not sub_result(result, "contains_letters").passed

    def test_pass_multiple_report_nums(self):
        assert ReportNumIsValid.check("ECTP-2024-05; WLCAPP-2024-05; FUE-2024-05").passed

    def test_warn_too_long(self):
        result = ReportNumIsValid.check("X" * 2001)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_warn_contains_url(self):
        result = ReportNumIsValid.check("https://example.com/report")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_http_url(self):
        result = ReportNumIsValid.check("http://example.com/report")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi(self):
        result = ReportNumIsValid.check("doi:10.1234/abc123")
        assert result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_warn_no_letters(self):
        result = ReportNumIsValid.check("1234567")
        assert result.passed
        assert not sub_result(result, "contains_letters").passed

    def test_warn_no_digits(self):
        result = ReportNumIsValid.check("ABCDEFG")
        assert result.passed
        assert not sub_result(result, "contains_digits").passed

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
        assert result.check_config["id"] == 550
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT
