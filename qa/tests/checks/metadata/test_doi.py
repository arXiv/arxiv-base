"""Tests for DoiIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, Inputs, Result
from qa.checks.metadata.doi import DoiIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestDoiIsValid:
    def test_pass_normal(self):
        assert DoiIsValid.check("10.1103/PhysRevLett.132.011001").passed

    def test_pass_none(self):
        assert DoiIsValid.check(None).passed

    def test_pass_empty(self):
        assert DoiIsValid.check("").passed

    def test_pass_none_has_no_sub_results(self):
        result = DoiIsValid.check(None)
        assert result.results == []

    def test_warn_too_short(self):
        result = DoiIsValid.check("10.1/abc")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_too_long(self):
        result = DoiIsValid.check("10.1103/" + "a" * 1993)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_warn_bad_doi_prefix_doi_colon(self):
        result = DoiIsValid.check("doi:10.1103/PhysRevLett.132.011001")
        assert result.passed
        assert not sub_result(result, "does_not_contain_bad_doi_prefix").passed

    def test_warn_bad_doi_prefix_https(self):
        result = DoiIsValid.check("https://doi.org/10.1103/PhysRevLett.132.011001")
        assert result.passed
        assert not sub_result(result, "does_not_contain_bad_doi_prefix").passed

    def test_warn_invalid_doi(self):
        result = DoiIsValid.check("not-a-doi")
        assert result.passed
        assert not sub_result(result, "doi_has_valid_format").passed

    def test_warn_contains_url(self):
        result = DoiIsValid.check("https://example.com/10.1103/something")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi_text(self):
        result = DoiIsValid.check("doi:10.1103/PhysRevLett.132.011001")
        assert result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_warn_leading_whitespace(self):
        result = DoiIsValid.check(" 10.1103/PhysRevLett.132.011001")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = DoiIsValid.check("10.1103/PhysRevLett.132.011001  10.1103/PhysRevLett.132.011002")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_control_chars(self):
        result = DoiIsValid.check("10.1103/PhysRev\tLett.132.011001")
        assert result.passed
        assert not sub_result(result, "does_not_contain_control_chars").passed

    def test_all_sub_checks_run_on_valid(self):
        result = DoiIsValid.check("10.1103/PhysRevLett.132.011001")
        assert result.results is not None
        assert len(result.results) == len(DoiIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            DoiIsValid().run(Inputs())

    def test_result_has_check_metadata(self):
        result = DoiIsValid.check("10.1103/PhysRevLett.132.011001")
        assert result.check_name == "doi_is_valid"
        assert result.check_id == 570
        assert result.check_version == "1.0.0"
        assert result.on_failure_policy == OnFailurePolicy.REJECT
