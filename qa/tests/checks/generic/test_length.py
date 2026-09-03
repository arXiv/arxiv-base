"""Tests for generic length checks."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.length import NotTooLong, NotTooShort


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestBaseGenericCheckValidation:
    check = make(NotTooShort, min_chars=5)

    def test_missing_data_raises(self):
        with pytest.raises(MissingDataError):
            self.check.run(QaDataRegistry())


class TestNotTooShort:
    check = make(NotTooShort, min_chars=5)

    def test_pass_exact(self):
        assert self.check.run(inputs("abcde")).passed

    def test_pass_longer(self):
        assert self.check.run(inputs("A fine title")).passed

    def test_fail(self):
        result = self.check.run(inputs("abcd"))
        assert not result.passed
        assert result.offsets[0].start == 0
        assert result.offsets[0].end == 4

    def test_fail_offset(self):
        result = self.check.run(inputs("ab"))
        assert result.offsets[0].end == 2

    def test_default_failure_message(self):
        result = self.check.run(inputs("ab"))
        assert result.message == "Too short."

    def test_custom_failure_message(self):
        check = make(NotTooShort, min_chars=5, failure_message="Custom short message.")
        result = check.run(inputs("ab"))
        assert result.message == "Custom short message."
        assert check.config["failure_message"] == "Custom short message."


class TestNotTooLong:
    check = make(NotTooLong, max_chars=10)

    def test_pass_exact(self):
        assert self.check.run(inputs("a" * 10)).passed

    def test_pass_shorter(self):
        assert self.check.run(inputs("hello")).passed

    def test_fail(self):
        result = self.check.run(inputs("a" * 11))
        assert not result.passed
        assert result.offsets[0].start == 10
        assert result.offsets[0].end == 11

    def test_config_includes_max_chars(self):
        assert self.check.config["max_chars"] == 10

    def test_custom_failure_message(self):
        check = make(NotTooLong, max_chars=10, failure_message="Custom long message.")
        result = check.run(inputs("a" * 11))
        assert result.message == "Custom long message."
        assert check.config["failure_message"] == "Custom long message."
