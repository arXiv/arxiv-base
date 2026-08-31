"""Tests for CommentsAreValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry, Result, Disposition
from qa.checks.metadata.comments import CommentsAreValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestCommentsAreValid:
    def test_pass_normal(self):
        assert CommentsAreValid.check("12 pages, 3 figures").passed

    def test_pass_none(self):
        result = CommentsAreValid.check(None)
        assert not result.passed
        assert result.disposition == Disposition.OK
        assert result.results is not None
        assert len(result.results) == 1
        assert result.results[0].check_config["name"] == "field_is_not_empty"

    def test_pass_empty(self):
        result = CommentsAreValid.check("")
        assert not result.passed
        assert result.disposition == Disposition.OK
        assert result.results is not None
        assert len(result.results) == 1
        assert result.results[0].check_config["name"] == "field_is_not_empty"

    def test_fail_too_long(self):
        result = CommentsAreValid.check("x" * 1001)
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_max_length(self):
        assert CommentsAreValid.check("x" * 1000).passed

    def test_fail_linebreak(self):
        result = CommentsAreValid.check("12 pages, \\\\ 3 figures")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_linebreak").passed

    def test_fail_all_caps(self):
        result = CommentsAreValid.check("TWELVE PAGES AND THREE FIGURES")
        assert not result.passed
        assert not sub_result(result, "not_all_caps").passed

    def test_pass_control_chars_without_cleanup(self):
        """Control characters are only normalized via cleanup(); check() no longer rejects them directly."""
        assert CommentsAreValid.check("12 pages\twith tab").passed

    def test_pass_ends_with_period_without_cleanup(self):
        """A trailing period is only removed via cleanup(); check() no longer rejects it directly."""
        assert CommentsAreValid.check("12 pages, 3 figures.").passed

    def test_warn_utf8_decoding_error_accents(self):
        result = CommentsAreValid.check("A comment with èéêëìíîï accents".encode("UTF-8").decode("LATIN-1"))
        assert not result.passed
        assert not sub_result(result, "no_utf8_decoding_errors").passed

    def test_warn_utf8_decoding_error_chinese(self):
        result = CommentsAreValid.check("A comment with 普通话 Chinese".encode("UTF-8").decode("LATIN-1"))
        assert not result.passed
        assert not sub_result(result, "no_utf8_decoding_errors").passed

    def test_all_sub_checks_run_on_valid(self):
        result = CommentsAreValid.check("12 pages, 3 figures")
        assert result.results is not None
        assert len(result.results) == len(CommentsAreValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            CommentsAreValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = CommentsAreValid.check("12 pages, 3 figures")
        assert result.check_config["name"] == "comments_are_valid"
        assert result.check_config["id"] == 400
        assert result.check_config["version"] == "1.0.0"


class TestCleanup:
    def test_collapses_whitespace_and_strips(self):
        assert CommentsAreValid.cleanup("  12 pages, 3 figures.  ") == "12 pages, 3 figures"

    def test_removes_trailing_periods(self):
        assert CommentsAreValid.cleanup("12   pages...") == "12 pages"

    def test_removes_control_chars(self):
        assert CommentsAreValid.cleanup("12 pages\twith tab") == "12 pages with tab"

    def test_removes_space_before_comma(self):
        assert CommentsAreValid.cleanup("12 pages , 3 figures") == "12 pages, 3 figures"

    def test_removes_unnecessary_space_in_parens(self):
        assert CommentsAreValid.cleanup("12 pages ( draft )") == "12 pages (draft)"
