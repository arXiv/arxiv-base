"""Tests for generic capitalization checks."""

from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.casing import DoesNotStartWithLowercase, NoExcessiveCapitals


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestNoExcessiveCapitals:
    check = make(NoExcessiveCapitals)

    def test_pass_normal(self):
        assert self.check.run(inputs("A fine title")).passed

    def test_pass_borderline(self):
        assert self.check.run(inputs("BORDERLINE All Caps TITLE")).passed

    def test_fail_all_caps(self):
        assert not self.check.run(inputs("ALL CAPS TITLE")).passed

    def test_fail_not_even_borderline(self):
        assert not self.check.run(inputs("NOT EVEN BORDERLINE ALL CAPS TITLE")).passed

    def test_fail_greek_caps(self):
        assert not self.check.run(inputs("ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΎ")).passed


class TestDoesNotStartWithLowercase:
    check = make(DoesNotStartWithLowercase)

    def test_pass(self):
        assert self.check.run(inputs("A title")).passed

    def test_fail(self):
        assert not self.check.run(inputs("a title with lowercase")).passed

    def test_fail_mixed(self):
        assert not self.check.run(inputs("aTITLE: Not So Lowercase")).passed

    def test_pass_digit_start(self):
        assert self.check.run(inputs("2D materials")).passed
