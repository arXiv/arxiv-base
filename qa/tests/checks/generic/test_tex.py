"""Tests for generic TeX/LaTeX checks."""

from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.tex import (
    DoesNotContainLinebreak,
    DoesNotContainHrefOrUrlTex,
    DoesNotContainUnnecessaryEscape,
)


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestDoesNotContainLinebreak:
    check = make(DoesNotContainLinebreak)

    def test_pass(self):
        assert self.check.run(inputs("This \\ is not a line break")).passed

    def test_fail(self):
        result = self.check.run(inputs("Line break at end\\\\"))
        assert not result.passed
        assert len(result.offsets) == 1

    def test_fail_mid_string(self):
        assert not self.check.run(inputs("before\\\\after")).passed


class TestDoesNotContainUnnecessaryEscape:
    check = make(DoesNotContainUnnecessaryEscape)

    def test_pass(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_fail_hash(self):
        result = self.check.run(inputs("contains \\# escape"))
        assert not result.passed
        assert len(result.offsets) == 1

    def test_fail_percent(self):
        assert not self.check.run(inputs("contains \\% escape")).passed

    def test_fail_dollar(self):
        assert not self.check.run(inputs("contains \\$ escape")).passed

    def test_fail_underscore(self):
        assert not self.check.run(inputs("contains \\_ escape")).passed

    def test_pass_regular_backslash(self):
        assert self.check.run(inputs("a \\command title")).passed

    def test_pass_unescaped_underscore(self):
        assert self.check.run(inputs("a title with a_variable name")).passed


class TestDoesNotContainHrefOrUrlTex:
    check = make(DoesNotContainHrefOrUrlTex)

    def test_pass(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_fail_href(self):
        assert not self.check.run(inputs("contains \\href{url} text")).passed

    def test_fail_url(self):
        assert not self.check.run(inputs("contains \\url{http://example.com}")).passed

    def test_fail_case_insensitive(self):
        assert not self.check.run(inputs("contains \\HREF{url} text")).passed
