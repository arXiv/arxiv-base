"""Tests for EmptyFieldCheck."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Disposition, QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.presence import EmptyFieldCheck


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(**kwargs):
    return EmptyFieldCheck(data="metadata", field="title", **kwargs)


class TestEmptyFieldCheck:
    def test_short_circuits_on_failure(self):
        assert EmptyFieldCheck._short_circuits_on_failure is True

    def test_missing_data_raises(self):
        check = make(on_failure_policy=OnFailurePolicy.REJECT)
        with pytest.raises(MissingDataError):
            check.run(QaDataRegistry())

    def test_fail_none(self):
        check = make(on_failure_policy=OnFailurePolicy.REJECT)
        result = check.run(inputs(None))
        assert not result.passed
        assert result.disposition == Disposition.REJECT

    def test_fail_empty(self):
        check = make(on_failure_policy=OnFailurePolicy.REJECT)
        result = check.run(inputs(""))
        assert not result.passed
        assert result.disposition == Disposition.REJECT

    def test_fail_empty_ignored(self):
        """An IGNORE policy still fails the check but produces an OK disposition."""
        check = make(on_failure_policy=OnFailurePolicy.IGNORE)
        result = check.run(inputs(""))
        assert not result.passed
        assert result.disposition == Disposition.OK

    def test_pass_with_value(self):
        check = make(on_failure_policy=OnFailurePolicy.REJECT)
        result = check.run(inputs("A fine title"))
        assert result.passed
        assert result.message == ""

    def test_custom_failure_message(self):
        check = make(on_failure_policy=OnFailurePolicy.REJECT, failure_message="Custom message.")
        result = check.run(inputs(""))
        assert result.message == "Custom message."
