"""Tests for JournalRefIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result
from qa.checks.metadata.journal_ref import JournalRefIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


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

    def test_fail_too_long(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001 (2024) " + "x" * 250)
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_length_limit(self):
        assert JournalRefIsValid.check("Phys. Rev. Lett. (2024) " + "x" * 216).passed

    def test_warn_contains_url(self):
        result = JournalRefIsValid.check("https://journals.aps.org/prl/abstract (2024)")
        assert result.passed
        assert not sub_result(result, "does_not_contain_url").passed

    def test_warn_contains_doi(self):
        result = JournalRefIsValid.check("doi:10.1103/PhysRevLett.132.011001 (2024)")
        assert result.passed
        assert not sub_result(result, "does_not_contain_doi").passed

    def test_fail_contains_bare_doi(self):
        result = JournalRefIsValid.check("10.1103/PhysRevLett.132.011001")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_bare_doi").passed

    def test_fail_contains_accepted(self):
        result = JournalRefIsValid.check("accepted by Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_accepted").passed

    def test_fail_contains_accept_stem(self):
        result = JournalRefIsValid.check("acceptance pending at Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_accepted").passed

    def test_fail_contains_submitted(self):
        result = JournalRefIsValid.check("submitted to Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_submitted").passed

    def test_fail_contains_submit_stem(self):
        result = JournalRefIsValid.check("submitting to Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_submitted").passed

    def test_fail_contains_in_press(self):
        result = JournalRefIsValid.check("in press, Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_in_press").passed

    def test_fail_contains_appear(self):
        result = JournalRefIsValid.check("to appear in Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_appear").passed

    def test_fail_contains_to_be_published(self):
        result = JournalRefIsValid.check("to be published in Phys. Rev. Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_to_be_published").passed

    def test_warn_contains_bibtex(self):
        result = JournalRefIsValid.check("title=Some Title, booktitle=Proceedings (2024)")
        assert result.passed
        assert not sub_result(result, "does_not_contain_bibtex").passed

    def test_fail_missing_year(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001")
        assert not result.passed
        assert not sub_result(result, "journal_ref_contains_valid_year").passed

    def test_pass_year_at_string_start(self):
        assert JournalRefIsValid.check("2024, Phys. Rev. Lett. 132").passed

    def test_fail_trailing_period(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. 132, 011001 (2024).")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_trailing_period").passed

    def test_fail_rightarrow_macro(self):
        result = JournalRefIsValid.check("Phys. Rev. Lett. (2024), A \\rightarrow B")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_rightarrow_macro").passed

    def test_fail_tex_hard_space_after_period(self):
        result = JournalRefIsValid.check("Phys. Rev.~Lett. (2024)")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_tex_hard_space_after_period").passed

    def test_fail_url_ends_with_period(self):
        result = JournalRefIsValid.check("(2024) see http://example.com/prl.")
        assert not result.passed
        assert not sub_result(result, "url_does_not_end_with_period").passed

    def test_fail_too_many_lines(self):
        journal_ref = "\n".join(["Phys. Rev. Lett. (2024)", "line two", "line three", "line four"])
        result = JournalRefIsValid.check(journal_ref)
        assert not result.passed
        assert not sub_result(result, "not_too_many_lines").passed

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
