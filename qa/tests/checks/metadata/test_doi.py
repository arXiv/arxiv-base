"""Tests for DoiIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result
from qa.checks.metadata.doi import DoiIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestDoiIsValid:
    def test_pass_normal(self):
        assert DoiIsValid.check("10.1103/PhysRevLett.132.011001").passed

    def test_pass_none(self):
        result = DoiIsValid.check(None)
        assert result.passed
        assert result.results == []

    def test_pass_empty(self):
        result = DoiIsValid.check("")
        assert result.passed
        assert result.results == []

    def test_fail_too_short(self):
        result = DoiIsValid.check("10.1/abc")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_too_long(self):
        result = DoiIsValid.check("10.1103/" + "a" * 43)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_max_length(self):
        assert DoiIsValid.check("10.1103/" + "a" * 42).passed

    def test_fail_bad_doi_prefix_doi_colon(self):
        result = DoiIsValid.check("doi:10.1103/PhysRevLett.132.011001")
        assert not result.passed
        assert not sub_result(result, "does_not_begin_with_doi_prefix").passed

    def test_fail_bad_doi_prefix_https(self):
        result = DoiIsValid.check("https://doi.org/10.1103/PhysRevLett.132.011001")
        assert not result.passed
        assert not sub_result(result, "does_not_begin_with_doi_prefix").passed

    def test_pass_non_ten_prefix(self):
        assert DoiIsValid.check("22.48550/arXiv.2501.18183").passed

    def test_warn_invalid_doi(self):
        result = DoiIsValid.check("definitely-invalid")
        assert result.passed
        assert not sub_result(result, "doi_has_valid_format").passed

    def test_fail_invalid_doi_no_scheme(self):
        result = DoiIsValid.check("doi.org/10.48550/arXiv.2501.18183")
        assert not result.passed
        assert not sub_result(result, "doi_has_valid_format").passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_pass_doi_without_registrant_code(self):
        # Per the DOI spec, the registrant code is optional: a directory indicator
        # followed directly by "/" and a suffix is a syntactically valid prefix.
        assert DoiIsValid.check("10/abcdefghij").passed

    def test_pass_doi_with_multi_segment_registrant_code(self):
        # Per the DOI spec, the registrant code may itself contain multiple
        # period-separated digit sequences (e.g. "10.500.100").
        assert DoiIsValid.check("10.500.100/suffix").passed

    def test_warn_invalid_doi_with_preceding_text(self):
        result = DoiIsValid.check("I like 10.48550/arXiv.2501.18183")
        assert result.passed
        assert not sub_result(result, "doi_has_valid_format").passed

    def test_fail_contains_url(self):
        result = DoiIsValid.check("https://example.com/10.1103/something")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_fail_contains_doi_text(self):
        result = DoiIsValid.check("doi:10.1103/PhysRevLett.132.011001")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_all_sub_checks_run_on_valid(self):
        result = DoiIsValid.check("10.1103/PhysRevLett.132.011001")
        assert result.results is not None
        assert len(result.results) == len(DoiIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            DoiIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = DoiIsValid.check("10.1103/PhysRevLett.132.011001")
        assert result.check_config["name"] == "doi_is_valid"
        assert result.check_config["id"] == 700
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT


class TestCleanup:
    def test_collapses_whitespace_and_strips(self):
        result = DoiIsValid.cleanup("  10.1103/PhysRevLett.132.011001   extra  ")
        assert result == "10.1103/PhysRevLett.132.011001 extra"
