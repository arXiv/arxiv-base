"""Tests for generic control character and encoding checks."""

from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.encoding import DoesNotContainControlChars, NoUtf8DecodingErrors


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestDoesNotContainControlChars:
    check = make(DoesNotContainControlChars)

    def test_pass(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_fail_tab(self):
        assert not self.check.run(inputs("A title\twith tab")).passed

    def test_fail_newline(self):
        assert not self.check.run(inputs("A title\nwith newline")).passed

    def test_fail_null(self):
        assert not self.check.run(inputs("A title\x00with null")).passed


class TestNoUtf8DecodingErrors:
    check = make(NoUtf8DecodingErrors)

    def test_pass_ascii(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_pass_valid_unicode(self):
        assert self.check.run(inputs("A title with émojis and ñoño")).passed

    def test_fail_malformed(self):
        result = self.check.run(inputs("Bad \xc0\x80 encoding"))
        assert not result.passed
