"""Tests for CommentsAreValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, Inputs, Result
from qa.checks.metadata.comments import CommentsAreValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestCommentsAreValid:
    def test_pass_normal(self):
        assert CommentsAreValid.check("12 pages, 3 figures").passed

    def test_pass_none(self):
        assert CommentsAreValid.check(None).passed

    def test_pass_empty(self):
        assert CommentsAreValid.check("").passed

    def test_pass_none_has_no_sub_results(self):
        result = CommentsAreValid.check(None)
        assert result.results == []

    def test_warn_too_long(self):
        result = CommentsAreValid.check("x" * 10001)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_warn_linebreak(self):
        result = CommentsAreValid.check("12 pages\\\\3 figures")
        assert result.passed
        assert not sub_result(result, "does_not_contain_linebreak").passed

    def test_warn_excessive_caps(self):
        result = CommentsAreValid.check("ALL CAPS COMMENTS")
        assert result.passed
        assert not sub_result(result, "no_excessive_capitals").passed

    def test_warn_unnecessary_escape(self):
        result = CommentsAreValid.check("contains \\% escape")
        assert result.passed
        assert not sub_result(result, "does_not_contain_unnecessary_escape").passed

    def test_warn_tex(self):
        result = CommentsAreValid.check("see \\href{url}{text}")
        assert result.passed
        assert not sub_result(result, "does_not_contain_tex").passed

    def test_warn_leading_whitespace(self):
        result = CommentsAreValid.check(" Leading space")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_trailing_whitespace(self):
        result = CommentsAreValid.check("Trailing space ")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = CommentsAreValid.check("12  pages, 3 figures")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_space_in_parens(self):
        result = CommentsAreValid.check("submitted to ( journal)")
        assert result.passed
        assert not sub_result(result, "no_unnecessary_space_in_parens").passed

    def test_warn_unbalanced_brackets(self):
        result = CommentsAreValid.check("12 pages (3 figures")
        assert result.passed
        assert not sub_result(result, "all_brackets_balanced").passed

    def test_warn_control_chars(self):
        result = CommentsAreValid.check("12 pages\twith tab")
        assert result.passed
        assert not sub_result(result, "does_not_contain_control_chars").passed

    def test_all_sub_checks_run_on_valid(self):
        result = CommentsAreValid.check("12 pages, 3 figures")
        assert result.results is not None
        assert len(result.results) == len(CommentsAreValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            CommentsAreValid().run(Inputs())

    def test_result_has_check_metadata(self):
        result = CommentsAreValid.check("12 pages, 3 figures")
        assert result.check_name == "comments_are_valid"
        assert result.check_id == 6
        assert result.check_version == "1.0.0"
        assert result.on_failure_policy == OnFailurePolicy.REJECT
