"""Tests for generic structural integrity checks (brackets, HTML)."""

from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.structure import (
    AllBracketsBalanced,
    DoesNotContainHtmlEscapes,
    DoesNotContainUnacceptableHtmlTags,
    NoHtmlElements,
)


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

    def test_fail_hr(self):
        assert not self.check.run(inputs("A title<hr/>with a rule")).passed

    def test_fail_em(self):
        assert not self.check.run(inputs("A title with <em>emphasis</em>")).passed

    def test_fail_strong(self):
        assert not self.check.run(inputs("A title with <strong>emphasis</strong>")).passed


class TestDoesNotContainHtmlEscapes:
    check = make(DoesNotContainHtmlEscapes)

    def test_pass(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_fail_named_entity(self):
        result = self.check.run(inputs("Fish &amp; chips"))
        assert not result.passed

    def test_fail_decimal_entity(self):
        result = self.check.run(inputs("A title with &#38; an entity"))
        assert not result.passed

    def test_fail_hex_entity(self):
        result = self.check.run(inputs("A title with &#x26; an entity"))
        assert not result.passed

    def test_pass_bare_ampersand(self):
        """A bare ampersand without a trailing semicolon is not an HTML escape."""
        assert self.check.run(inputs("Fish & chips")).passed


class TestDoesNotContainUnacceptableHtmlTags:
    check = make(DoesNotContainUnacceptableHtmlTags)

    def test_pass_no_html(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_pass_bare_ampersand(self):
        """bleach escapes a bare ampersand (making it longer), not strips it - should still pass."""
        assert self.check.run(inputs("Fish & chips")).passed

    def test_pass_allowed_tag(self):
        assert self.check.run(inputs("Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>")).passed

    def test_pass_allowed_em(self):
        assert self.check.run(inputs("Title with <em>emphasis</em>")).passed

    def test_fail_p_tag(self):
        result = self.check.run(inputs("A title with <p>paragraph</p>"))
        assert not result.passed

    def test_fail_div(self):
        result = self.check.run(inputs("A <div>wrapped</div> title"))
        assert not result.passed

    def test_fail_script(self):
        result = self.check.run(inputs("A title with <script>alert(1)</script>"))
        assert not result.passed

    def test_pass_h_tag(self):
        result = self.check.run(inputs("A title with <h>heading</h>"))
        assert result.passed


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
