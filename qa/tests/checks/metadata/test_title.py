"""Tests for TitleIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, Inputs, Metadata, Result
from qa.checks.metadata.title import TitleIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestTitleIsValid:
    def test_pass_normal(self):
        result = TitleIsValid.check("A fine title")
        assert result.passed

    def test_pass_with_known_caps(self):
        result = TitleIsValid.check("Another title about CERN and ALPEH where z~1/2")
        assert result.passed

    def test_fail_empty(self):
        result = TitleIsValid.check("")
        assert not result.passed

    def test_fail_empty_has_sub_results(self):
        result = TitleIsValid.check("")
        not_empty = sub_result(result, "not_empty")
        assert not not_empty.passed

    def test_warn_too_short(self):
        result = TitleIsValid.check("Tiny")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_pass_ends_with_punctuation(self):
        result = TitleIsValid.check("A title with period.")
        assert result.passed

    def test_pass_digit_strings_not_caps(self):
        result = TitleIsValid.check("The is a title with 12345678 and 987654321 words not capitalized")
        assert result.passed

    def test_pass_short_html_like_tags(self):
        result = TitleIsValid.check("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>")
        assert result.passed

    def test_warn_begins_with_title(self):
        result = TitleIsValid.check("Title: Something")
        assert result.passed
        assert not sub_result(result, "does_not_begin_with_title").passed

    def test_pass_single_backslash(self):
        result = TitleIsValid.check("This \\ is not a line break")
        assert result.passed

    def test_pass_complex_parens(self):
        result = TitleIsValid.check("Something about sin(x), H2(SO)4, and (Non-)Commutative operations")
        assert result.passed

    def test_pass_greek(self):
        result = TitleIsValid.check("Προγραμματισμού")
        assert result.passed

    def test_pass_long_greek(self):
        title = "Αν Ήταν Εφικτό Να Συμπτυχθεί Ολόκληρη Η Γη Σε Μια Ακτίνα 0,9 Εκατοστών, Δηλαδή Στο Μέγεθος Ενός Κερασιού, Θα Είχε Μετατραπεί Σε Μαύρη Τρύπα. Η C Είναι Μια Σχετικά Μινιμαλιστική Γλώσσα Προγραμματισμού. Η Μνήμη Ενός Κλασικού Ψηφιακού Υπολογισ"
        result = TitleIsValid.check(title)
        assert result.passed

    def test_all_sub_checks_run_on_empty(self):
        result = TitleIsValid.check("")
        assert result.results is not None
        assert len(result.results) == len(TitleIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            TitleIsValid().run(Inputs())

    def test_none_title_raises(self):
        with pytest.raises(MissingDataError):
            TitleIsValid().run(Inputs(metadata=Metadata(title=None)))

    def test_result_has_check_metadata(self):
        result = TitleIsValid.check("A fine title")
        assert result.check_config["name"] == "title_is_valid"
        assert result.check_config["id"] == 500
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT

    def test_fail_on_failure_policy_reject(self):
        assert TitleIsValid.check("").check_config["on_failure_policy"] == OnFailurePolicy.REJECT

