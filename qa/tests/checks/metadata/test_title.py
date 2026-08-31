"""Tests for TitleIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Disposition, QaDataRegistry, Metadata, Result
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

    def test_fail_empty_short_circuits(self):
        result = TitleIsValid.check("")
        assert not result.passed
        assert result.results is not None
        assert len(result.results) == 1
        assert not result.results[0].passed
        assert result.results[0].disposition == Disposition.REJECT

    def test_warn_too_short(self):
        result = TitleIsValid.check("Ti")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_fail_too_long(self):
        result = TitleIsValid.check("x" * 301)
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_max_length(self):
        assert TitleIsValid.check("X" + "x" * 299).passed

    def test_pass_ends_with_punctuation(self):
        result = TitleIsValid.check("A title with period.")
        assert result.passed

    def test_warn_all_caps(self):
        result = TitleIsValid.check("A TITLE IN ALL CAPS")
        assert not result.passed
        assert not sub_result(result, "not_all_caps").passed

    def test_pass_digit_strings_not_caps(self):
        result = TitleIsValid.check("The is a title with 12345678 and 987654321 words not capitalized")
        assert result.passed

    def test_pass_short_html_like_tags(self):
        result = TitleIsValid.check("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>")
        assert result.passed

    def test_pass_begins_with_title_without_cleanup(self):
        """A leading 'title:' prefix is only stripped via cleanup(); check() no longer rejects it directly."""
        assert TitleIsValid.check("Title: Something").passed

    def test_pass_single_backslash(self):
        result = TitleIsValid.check("This \\ is not a line break")
        assert result.passed

    def test_fail_tex_linebreak(self):
        result = TitleIsValid.check("Line break at end\\\\")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_linebreak").passed

    def test_pass_raw_newline_without_cleanup(self):
        """A raw newline is only normalized via cleanup(); check() no longer rejects it directly."""
        assert TitleIsValid.check("A title with\na raw newline").passed

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

    def test_none_field_short_circuits(self):
        result = TitleIsValid().run(QaDataRegistry(metadata=Metadata(title=None)))
        assert not result.passed
        assert result.results is not None
        assert len(result.results) == 1
        assert not result.results[0].passed
        assert result.results[0].disposition == Disposition.REJECT

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            TitleIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = TitleIsValid.check("A fine title")
        assert result.check_config["name"] == "title_is_valid"
        assert result.check_config["id"] == 100
        assert result.check_config["version"] == "1.0.0"

    def test_fail_gives_reject_disposition(self):
        assert TitleIsValid.check("").disposition == Disposition.REJECT

    def test_fail_empty_messages_are_not_empty(self):
        """_messages() should surface a reason even when the field itself is empty."""
        assert TitleIsValid.check("")._messages(Disposition.REJECT) != ""


class TestCleanup:
    def test_collapses_whitespace_and_strips(self):
        assert TitleIsValid.cleanup("  A   title  with   spaces  ") == "A title with spaces"

    def test_strips_leading_title_colon_prefix(self):
        assert TitleIsValid.cleanup("Title: Something") == "Something"

    def test_does_not_strip_title_prefix_without_colon(self):
        assert TitleIsValid.cleanup("Title Something") == "Title Something"

    def test_does_not_strip_title_like_word(self):
        assert TitleIsValid.cleanup("Titleist irons review") == "Titleist irons review"

    def test_converts_raw_newline_to_space(self):
        assert TitleIsValid.cleanup("A title with\na raw newline") == "A title with a raw newline"

    def test_removes_control_chars(self):
        assert TitleIsValid.cleanup("A title\x00with control") == "A title with control"

    def test_removes_space_before_comma(self):
        assert TitleIsValid.cleanup("A title , with comma") == "A title, with comma"

    def test_removes_unnecessary_space_in_parens(self):
        assert TitleIsValid.cleanup("A title ( draft )") == "A title (draft)"
