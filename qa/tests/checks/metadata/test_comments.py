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

    def test_warn_too_long(self):
        result = CommentsAreValid.check("x" * 10001)
        assert result.passed
        assert not sub_result(result, "not_too_long").passed

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
        assert result.check_config["id"] == 530
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT
