"""Tests for MscClassIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, Inputs, Result
from qa.checks.metadata.msc_class import MscClassIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestMscClassIsValid:
    def test_pass_normal(self):
        assert MscClassIsValid.check("35K55; 65M06").passed

    def test_pass_none(self):
        assert MscClassIsValid.check(None).passed

    def test_pass_empty(self):
        assert MscClassIsValid.check("").passed

    def test_pass_none_has_no_sub_results(self):
        result = MscClassIsValid.check(None)
        assert result.results == []

    def test_warn_too_long(self):
        result = MscClassIsValid.check("x" * 1001)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_warn_contains_url(self):
        result = MscClassIsValid.check("https://example.com/35K55")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi(self):
        result = MscClassIsValid.check("doi:10.1103/35K55")
        assert result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_warn_leading_whitespace(self):
        result = MscClassIsValid.check(" 35K55")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = MscClassIsValid.check("35K55  65M06")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_control_chars(self):
        result = MscClassIsValid.check("35K55\t65M06")
        assert result.passed
        assert not sub_result(result, "does_not_contain_control_chars").passed

    def test_warn_contains_semicolon(self):
        result = MscClassIsValid.check("35K55; 65M06")
        assert result.passed
        assert not sub_result(result, "does_not_contain_semicolon").passed

    def test_all_sub_checks_run_on_valid(self):
        result = MscClassIsValid.check("35K55")
        assert result.results is not None
        assert len(result.results) == len(MscClassIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            MscClassIsValid().run(Inputs())

    def test_result_has_check_metadata(self):
        result = MscClassIsValid.check("35K55")
        assert result.check_name == "msc_class_is_valid"
        assert result.check_id == 580
        assert result.check_version == "1.0.0"
        assert result.on_failure_policy == OnFailurePolicy.REJECT
