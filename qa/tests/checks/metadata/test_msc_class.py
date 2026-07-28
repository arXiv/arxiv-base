"""Tests for MscClassIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result
from qa.checks.metadata.msc_class import MscClassIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestMscClassIsValid:
    def test_pass_normal(self):
        assert MscClassIsValid.check("35K55; 65M06").passed

    def test_pass_none(self):
        result = MscClassIsValid.check(None)
        assert result.passed
        assert result.results == []

    def test_pass_empty(self):
        result = MscClassIsValid.check("")
        assert result.passed
        assert result.results == []

    def test_fail_too_long(self):
        result = MscClassIsValid.check("x" * 161)
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_length_limit(self):
        assert MscClassIsValid.check("x" * 160).passed

    def test_warn_contains_url(self):
        result = MscClassIsValid.check("https://example.com/35K55")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi(self):
        result = MscClassIsValid.check("doi:10.1103/35K55")
        assert result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_pass_semicolon_separated(self):
        assert MscClassIsValid.check("35K55; 65M06").passed

    def test_fail_msc_prefix(self):
        result = MscClassIsValid.check("MSC classification: 35K55")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_msc_prefix").passed

    def test_fail_msc_prefix_bare(self):
        result = MscClassIsValid.check("MSC 35K55")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_msc_prefix").passed

    def test_fail_trailing_period(self):
        result = MscClassIsValid.check("35K55.")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_trailing_period").passed

    def test_fail_too_many_lines(self):
        result = MscClassIsValid.check("35K55\n65M06\n14J60")
        assert not result.passed
        assert not sub_result(result, "not_too_many_lines").passed

    def test_pass_space_separated(self):
        assert MscClassIsValid.check("abc def").passed

    def test_pass_primary_secondary_notation(self):
        assert MscClassIsValid.check("14J60 (Primary) 14F05, 14J26 (Secondary)").passed

    def test_all_sub_checks_run_on_valid(self):
        result = MscClassIsValid.check("35K55")
        assert result.results is not None
        assert len(result.results) == len(MscClassIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            MscClassIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = MscClassIsValid.check("35K55")
        assert result.check_config["name"] == "msc_class_is_valid"
        assert result.check_config["id"] == 800
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT
