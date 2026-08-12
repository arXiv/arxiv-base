"""Tests for generic structural integrity checks (brackets, HTML)."""

from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.structure import AllBracketsBalanced, NoHtmlElements


def inputs(title: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestNoHtmlElements:
    check = make(NoHtmlElements)

    def test_pass(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_pass_short_tags(self):
        assert self.check.run(inputs("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>")).passed

    def test_fail_sup(self):
        result = self.check.run(inputs("Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>"))
        assert not result.passed

    def test_fail_br(self):
        assert not self.check.run(inputs("A title with HTML<br/>linebreaks<br />there")).passed

    def test_fail_p_tag(self):
        assert not self.check.run(inputs("A title with <p>paragraph</p>")).passed

    def test_fail_div(self):
        assert not self.check.run(inputs("A <div>wrapped</div> title")).passed


class TestAllBracketsBalanced:
    check = make(AllBracketsBalanced)

    def test_pass_no_brackets(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_pass_balanced(self):
        assert self.check.run(inputs("Something about sin(x), H2(SO)4, and (Non-)Commutative operations")).passed

    def test_pass_nested(self):
        assert self.check.run(inputs("A (nested [bracket {set}] here)")).passed

    def test_fail_nested(self):
        assert not self.check.run(inputs("[{}])}")).passed

    def test_fail_unclosed_paren(self):
        result = self.check.run(inputs("Unclosed (paren"))
        assert not result.passed
        assert result.offsets[0].start == 9

    def test_fail_unclosed_bracket(self):
        result = self.check.run(inputs("Unclosed [bracket"))
        assert not result.passed

    def test_fail_extra_close(self):
        result = self.check.run(inputs("Extra close) paren"))
        assert not result.passed
        assert result.offsets[0].start == 11

    def test_fail_mismatched(self):
        result = self.check.run(inputs("Mismatched (bracket]"))
        assert not result.passed
