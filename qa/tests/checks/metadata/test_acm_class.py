"""Tests for AcmClassIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry, Result, Disposition
from qa.checks.metadata.acm_class import AcmClassIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestAcmClassIsValid:
    def test_pass_normal(self):
        assert AcmClassIsValid.check("F.2.2").passed

    def test_pass_none(self):
        result = AcmClassIsValid.check(None)
        assert not result.passed
        assert result.disposition == Disposition.OK
        assert result.results is not None
        assert len(result.results) == 1
        assert result.results[0].check_config["name"] == "field_is_not_empty"

    def test_pass_empty(self):
        result = AcmClassIsValid.check("")
        assert not result.passed
        assert result.disposition == Disposition.OK
        assert result.results is not None
        assert len(result.results) == 1
        assert result.results[0].check_config["name"] == "field_is_not_empty"

    def test_pass_semicolon_separated_list(self):
        assert AcmClassIsValid.check("F.2.2; I.2.7").passed

    def test_fail_comma_separated_list(self):
        """cleanup() does not rewrite commas to semicolons; a comma is rejected outright."""
        result = AcmClassIsValid.check("F.2.2, I.2.7")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_comma").passed

    def test_warn_too_long(self):
        result = AcmClassIsValid.check("x" * 161)
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_max_length(self):
        assert AcmClassIsValid.check("x" * 160).passed

    def test_fail_contains_url(self):
        result = AcmClassIsValid.check("https://example.com/F.2.2")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_fail_contains_doi(self):
        result = AcmClassIsValid.check("doi:10.1103/F.2.2")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_pass_space_separated(self):
        assert AcmClassIsValid.check("abc def").passed

    def test_all_sub_checks_run_on_valid(self):
        result = AcmClassIsValid.check("F.2.2")
        assert result.results is not None
        assert len(result.results) == len(AcmClassIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            AcmClassIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = AcmClassIsValid.check("F.2.2")
        assert result.check_config["name"] == "acm_class_is_valid"
        assert result.check_config["id"] == 900
        assert result.check_config["version"] == "1.0.0"


class TestCleanup:
    def test_strips_and_uppercases(self):
        assert AcmClassIsValid.cleanup("  f.2.2  ") == "F.2.2"

    def test_strips_acm_class_prefix(self):
        assert AcmClassIsValid.cleanup("ACM-class: F.2.2") == "F.2.2"

    def test_does_not_convert_commas_to_semicolons(self):
        assert AcmClassIsValid.cleanup("F.2.2, I.2.7") == "F.2.2, I.2.7"

    def test_removes_trailing_period(self):
        assert AcmClassIsValid.cleanup("F.2.2.") == "F.2.2"

    def test_inserts_missing_period(self):
        assert AcmClassIsValid.cleanup("F2.2") == "F.2.2"

    def test_removes_control_chars(self):
        assert AcmClassIsValid.cleanup("F.2.2\x00I.2.7") == "F.2.2 I.2.7"

    def test_removes_unnecessary_space_in_parens(self):
        assert AcmClassIsValid.cleanup("F.2.2 ( see also )") == "F.2.2 (SEE ALSO)"
