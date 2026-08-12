"""Tests for generic field-prefix checks."""

import pytest

from qa.checks.base import EmptyFieldError, MissingDataError
from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.prefixes import DoesNotBeginWithTitle


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestBaseGenericPatternCheckValidation:
    check = make(DoesNotBeginWithTitle)

    def test_missing_data_raises(self):
        with pytest.raises(MissingDataError):
            self.check.run(QaDataRegistry())

    def test_none_field_raises(self):
        with pytest.raises(EmptyFieldError):
            self.check.run(inputs(None))

    def test_empty_field_raises(self):
        with pytest.raises(EmptyFieldError):
            self.check.run(inputs(""))


class TestDoesNotBeginWithTitle:
    check = make(DoesNotBeginWithTitle)

    def test_pass(self):
        assert self.check.run(inputs("A valid title")).passed

    def test_fail_title_colon(self):
        assert not self.check.run(inputs("Title: Something")).passed

    def test_fail_case_insensitive(self):
        assert not self.check.run(inputs("TITLE: Something")).passed

    def test_pass_title_mid_string(self):
        assert self.check.run(inputs("My title")).passed

