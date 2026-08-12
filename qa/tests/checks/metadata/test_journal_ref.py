"""Tests for JournalRefIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result
from qa.checks.metadata.journal_ref import JournalRefIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


def sub_result_by_max_chars(result: Result, max_chars: int) -> Result:
    assert result.results is not None
    return next(
        r
        for r in result.results
        if r.check_config["name"] == "not_too_long" and r.check_config["max_chars"] == max_chars
    )


class TestJournalRefIsValid:
    def test_pass_normal(self):
        assert JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001 (2024)").passed

    def test_pass_none(self):
        result = JournalRefIsValid.check(None)
        assert result.passed
        assert result.results == []

    def test_pass_empty(self):
        result = JournalRefIsValid.check("")
        assert result.passed
        assert result.results == []

    def test_warn_too_short(self):
        result = JournalRefIsValid.check("2024")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_fail_too_long_block(self):
        result = JournalRefIsValid.check("x" * 1600 + " 2024")
        assert not result.passed
        assert not sub_result_by_max_chars(result, 1500).passed
        assert sub_result_by_max_chars(result, 2000).passed

    def test_fail_too_long_block_and_warn(self):
        result = JournalRefIsValid.check("x" * 2001 + " 2024")
        assert not result.passed
        assert not sub_result_by_max_chars(result, 1500).passed
        assert not sub_result_by_max_chars(result, 2000).passed

    def test_fail_not_well_formed_no_year(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001")
        assert not result.passed
        assert not sub_result(result, "journal_ref_is_well_formed").passed

    def test_fail_contains_url(self):
        result = JournalRefIsValid.check("https://journals.aps.org/prl/abstract")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_fail_contains_doi(self):
        result = JournalRefIsValid.check("doi:10.1103/PhysRevLett.132.011001")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_fail_contains_bare_doi(self):
        result = JournalRefIsValid.check("10.1103/PhysRevLett.132.011001")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_bare_doi").passed

    def test_fail_contains_accepted(self):
        result = JournalRefIsValid.check("accepted by Phys. Rev. Lett.")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_accepted").passed

    def test_fail_contains_submitted(self):
        result = JournalRefIsValid.check("submitted to Phys. Rev. Lett.")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_submitted").passed

    def test_fail_contains_bibtex(self):
        result = JournalRefIsValid.check("title=Some Title, booktitle=Proceedings")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_bibtex").passed

    def test_all_sub_checks_run_on_valid(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001 (2024)")
        assert result.results is not None
        assert len(result.results) == len(JournalRefIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            JournalRefIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001 (2024)")
        assert result.check_config["name"] == "journal_ref_is_valid"
        assert result.check_config["id"] == 600
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT
