"""Tests for CommentsAreValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result
from qa.checks.metadata.comments import CommentsAreValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestCommentsAreValid:
    def test_pass_normal(self):
        assert CommentsAreValid.check("12 pages, 3 figures").passed

    def test_pass_none(self):
        result = CommentsAreValid.check(None)
        assert result.passed
        assert result.results == []

    def test_pass_empty(self):
        result = CommentsAreValid.check("")
        assert result.passed
        assert result.results == []

    def test_fail_too_long(self):
        result = CommentsAreValid.check("x" * 401)
        assert not result.passed
        assert not sub_result(result, "not_too_long").passed

    def test_pass_at_length_limit(self):
        assert CommentsAreValid.check("x" * 400).passed

    def test_fail_trailing_period(self):
        result = CommentsAreValid.check("12 pages, 3 figures.")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_trailing_period").passed

    def test_fail_rightarrow_macro(self):
        result = CommentsAreValid.check("Fixes A \\rightarrow B, should be \\to")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_rightarrow_macro").passed

    def test_fail_tex_hard_space_after_period(self):
        result = CommentsAreValid.check("See Fig.~2 for details")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_tex_hard_space_after_period").passed

    def test_fail_url_ends_with_period(self):
        result = CommentsAreValid.check("Code at http://example.com/repo.")
        assert not result.passed
        assert not sub_result(result, "url_does_not_end_with_period").passed

    def test_fail_too_many_lines(self):
        comments = "\n".join(f"Line {i}" for i in range(6))
        result = CommentsAreValid.check(comments)
        assert not result.passed
        assert not sub_result(result, "not_too_many_lines").passed

    def test_warn_utf8_decoding_error_accents(self):
        result = CommentsAreValid.check("A comment with èéêëìíîï accents".encode("UTF-8").decode("LATIN-1"))
        assert result.passed
        assert not sub_result(result, "no_utf8_decoding_errors").passed

    def test_warn_utf8_decoding_error_chinese(self):
        result = CommentsAreValid.check("A comment with 普通话 Chinese".encode("UTF-8").decode("LATIN-1"))
        assert result.passed
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
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT
