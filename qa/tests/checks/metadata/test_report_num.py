"""Tests for ReportNumIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, Inputs, Metadata, Result
from qa.checks.metadata.report_num import ReportNumIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestReportNumIsValid:
    def test_pass_normal(self):
        assert ReportNumIsValid.check("CERN-EP-2024-001").passed

    def test_pass_none(self):
        assert ReportNumIsValid.check(None).passed

    def test_pass_empty(self):
        assert ReportNumIsValid.check("").passed

    def test_pass_none_has_no_sub_results(self):
        result = ReportNumIsValid.check(None)
        assert result.results == []

    def test_warn_too_short(self):
        result = ReportNumIsValid.check("A1")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

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

    def test_warn_leading_whitespace(self):
        result = ReportNumIsValid.check(" CERN-EP-2024-001")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = ReportNumIsValid.check("CERN  EP 2024")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_control_chars(self):
        result = ReportNumIsValid.check("CERN\t2024-001")
        assert result.passed
        assert not sub_result(result, "does_not_contain_control_chars").passed

    def test_all_sub_checks_run_on_valid(self):
        result = ReportNumIsValid.check("CERN-EP-2024-001")
        assert result.results is not None
        assert len(result.results) == len(ReportNumIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            ReportNumIsValid().run(Inputs())

    def test_result_has_check_metadata(self):
        result = ReportNumIsValid.check("CERN-EP-2024-001")
        assert result.check_name == "report_num_is_valid"
        assert result.check_id == 8
        assert result.check_version == "1.0.0"
        assert result.on_failure_policy == OnFailurePolicy.REJECT
