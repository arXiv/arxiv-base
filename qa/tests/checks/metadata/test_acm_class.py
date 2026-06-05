"""Tests for AcmClassIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, Inputs, Result
from qa.checks.metadata.acm_class import AcmClassIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestAcmClassIsValid:
    def test_pass_normal(self):
        assert AcmClassIsValid.check("F.2.2; I.2.7").passed

    def test_pass_none(self):
        assert AcmClassIsValid.check(None).passed

    def test_pass_empty(self):
        assert AcmClassIsValid.check("").passed

    def test_pass_none_has_no_sub_results(self):
        result = AcmClassIsValid.check(None)
        assert result.results == []

    def test_warn_too_long(self):
        result = AcmClassIsValid.check("x" * 1001)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_warn_contains_url(self):
        result = AcmClassIsValid.check("https://example.com/F.2.2")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi(self):
        result = AcmClassIsValid.check("doi:10.1103/F.2.2")
        assert result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_pass_space_separated(self):
        assert AcmClassIsValid.check("abc def").passed

    def test_all_sub_checks_run_on_valid(self):
        result = AcmClassIsValid.check("F.2.2")
        assert result.results is not None
        assert len(result.results) == len(AcmClassIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            AcmClassIsValid().run(Inputs())

    def test_result_has_check_metadata(self):
        result = AcmClassIsValid.check("F.2.2")
        assert result.check_name == "acm_class_is_valid"
        assert result.check_id == 590
        assert result.check_version == "1.0.0"
        assert result.on_failure_policy == OnFailurePolicy.REJECT
