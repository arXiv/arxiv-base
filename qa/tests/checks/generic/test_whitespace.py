"""Tests for generic whitespace checks."""

from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.whitespace import NoExtraWhitespace, NoUnnecessarySpaceInParens


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestNoExtraWhitespace:
    check = make(NoExtraWhitespace)

    def test_pass(self):
        assert self.check.run(inputs("A title, with commas, properly spaced")).passed

    def test_pass_no_caught_comma_alpha(self):
        assert self.check.run(inputs("This is a title,bad title")).passed

    def test_fail_multiple_spaces(self):
        result = self.check.run(inputs("A title  with  multiple  spaces"))
        assert not result.passed

    def test_fail_trailing_before_newline(self):
        assert not self.check.run(inputs("A title  \nwith trailing")).passed

    def test_fail_space_before_comma(self):
        assert not self.check.run(inputs("This is a title , bad title")).passed

    def test_fail_double_comma(self):
        assert not self.check.run(inputs("This is a title, , bad title")).passed


class TestNoUnnecessarySpaceInParens:
    check = make(NoUnnecessarySpaceInParens)

    def test_pass(self):
        assert self.check.run(inputs("Something about sin(x)")).passed

    def test_fail_leading_space(self):
        result = self.check.run(inputs("Something ( with space"))
        assert not result.passed

    def test_fail_trailing_space(self):
        assert not self.check.run(inputs("Something (with space )")).passed

    def test_pass_complex(self):
        assert self.check.run(inputs("Something about sin(x), H2(SO)4, and (Non-)Commutative operations")).passed
