"""Tests for ValidTitleCheck."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Inputs, Metadata, Result
from qa.checks.metadata.title import ValidTitleCheck


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestValidTitleCheck:
    def test_pass_normal(self):
        result = ValidTitleCheck.check("A fine title")
        assert result.passed

    def test_pass_with_known_caps(self):
        result = ValidTitleCheck.check("Another title about CERN and ALPEH where z~1/2")
        assert result.passed

    def test_fail_empty(self):
        result = ValidTitleCheck.check("")
        assert not result.passed

    def test_fail_empty_has_sub_results(self):
        result = ValidTitleCheck.check("")
        not_empty = sub_result(result, "not_empty")
        assert not not_empty.passed

    def test_warn_too_short(self):
        result = ValidTitleCheck.check("Tiny")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_lowercase_start(self):
        result = ValidTitleCheck.check("a title with lowercase")
        assert result.passed
        assert not sub_result(result, "does_not_start_with_lowercase").passed

    def test_warn_lowercase_start_mixed(self):
        result = ValidTitleCheck.check("aTITLE: Not So Lowercase")
        assert result.passed
        assert not sub_result(result, "does_not_start_with_lowercase").passed

    def test_warn_leading_whitespace(self):
        result = ValidTitleCheck.check("  A title with leading space")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_trailing_whitespace(self):
        result = ValidTitleCheck.check("A title with trailing space ")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = ValidTitleCheck.check("A title  with  multiple  spaces")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_pass_ends_with_punctuation(self):
        result = ValidTitleCheck.check("A title with period.")
        assert result.passed

    def test_warn_excessive_caps(self):
        result = ValidTitleCheck.check("ALL CAPS TITLE")
        assert result.passed
        assert not sub_result(result, "no_excessive_capitals").passed

    def test_warn_not_even_borderline_caps(self):
        result = ValidTitleCheck.check("NOT EVEN BORDERLINE ALL CAPS TITLE")
        assert result.passed
        assert not sub_result(result, "no_excessive_capitals").passed

    def test_pass_borderline_caps(self):
        result = ValidTitleCheck.check("BORDERLINE All Caps TITLE")
        assert result.passed
        assert sub_result(result, "no_excessive_capitals").passed

    def test_warn_borderline_all_caps(self):
        result = ValidTitleCheck.check("BORDERLINE ALL caps TITLE")
        assert result.passed
        assert not sub_result(result, "no_excessive_capitals").passed

    def test_pass_one_long_caps_word(self):
        result = ValidTitleCheck.check("This is a title WITH ONE LONG WORD CAPITALIZED")
        assert result.passed
        assert sub_result(result, "no_unapproved_long_caps_words").passed

    def test_warn_two_unapproved_long_caps(self):
        result = ValidTitleCheck.check("This is a title WITH SOME EXTRAEXTRA LONG WORDS CAPITALIZED")
        assert result.passed
        assert not sub_result(result, "no_excessive_capitals").passed

    def test_pass_known_long_caps_words(self):
        result = ValidTitleCheck.check("The is a title with known long words capitalized AMANDA CHANDRA")
        assert result.passed
        assert sub_result(result, "no_unapproved_long_caps_words").passed

    def test_warn_unknown_long_caps_words(self):
        result = ValidTitleCheck.check("The is a title with unknown long words capitalized UNIQUEWORD THISISATEST")
        assert result.passed
        assert not sub_result(result, "no_unapproved_long_caps_words").passed

    def test_pass_digit_strings_not_caps(self):
        result = ValidTitleCheck.check("The is a title with 12345678 and 987654321 words not capitalized")
        assert result.passed

    def test_pass_short_html_like_tags(self):
        result = ValidTitleCheck.check("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>")
        assert result.passed

    def test_warn_html_sup(self):
        result = ValidTitleCheck.check("Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>")
        assert result.passed
        assert not sub_result(result, "no_html_elements").passed

    def test_warn_html_br(self):
        result = ValidTitleCheck.check("A title with HTML<br/>linebreaks<br />there")
        assert result.passed
        assert not sub_result(result, "no_html_elements").passed

    def test_warn_begins_with_title(self):
        result = ValidTitleCheck.check("Title: Something")
        assert result.passed
        assert not sub_result(result, "does_not_begin_with_title").passed

    def test_pass_single_backslash(self):
        result = ValidTitleCheck.check("This \\ is not a line break")
        assert result.passed

    def test_warn_linebreak(self):
        result = ValidTitleCheck.check("Line break at end\\\\")
        assert result.passed
        assert not sub_result(result, "does_not_contain_linebreak").passed

    def test_pass_complex_parens(self):
        result = ValidTitleCheck.check("Something about sin(x), H2(SO)4, and (Non-)Commutative operations")
        assert result.passed

    def test_pass_greek(self):
        result = ValidTitleCheck.check("Προγραμματισμού")
        assert result.passed

    def test_warn_greek_all_caps(self):
        result = ValidTitleCheck.check("ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΎ")
        assert result.passed
        assert not sub_result(result, "no_excessive_capitals").passed

    def test_pass_long_greek(self):
        title = "Αν Ήταν Εφικτό Να Συμπτυχθεί Ολόκληρη Η Γη Σε Μια Ακτίνα 0,9 Εκατοστών, Δηλαδή Στο Μέγεθος Ενός Κερασιού, Θα Είχε Μετατραπεί Σε Μαύρη Τρύπα. Η C Είναι Μια Σχετικά Μινιμαλιστική Γλώσσα Προγραμματισμού. Η Μνήμη Ενός Κλασικού Ψηφιακού Υπολογισ"
        result = ValidTitleCheck.check(title)
        assert result.passed

    def test_all_sub_checks_run_on_empty(self):
        result = ValidTitleCheck.check("")
        assert result.results is not None
        assert len(result.results) == len(ValidTitleCheck._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            ValidTitleCheck().run(Inputs())

    def test_none_title_raises(self):
        with pytest.raises(MissingDataError):
            ValidTitleCheck().run(Inputs(metadata=Metadata(title=None)))

    def test_result_has_check_metadata(self):
        result = ValidTitleCheck.check("A fine title")
        assert result.check_name == "valid_title_check"
        assert result.check_id == 0
        assert result.check_version == "1.0.0"

    def test_warn_double_comma(self):
        result = ValidTitleCheck.check("This is a title, , bad title")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_space_before_comma(self):
        result = ValidTitleCheck.check("This is a title , bad title")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed
