"""Tests for generic text checks."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Inputs, Metadata, OnFailurePolicy
from qa.checks.generic.text import (
    AllBracketsBalanced,
    DoesNotBeginWithTitle,
    DoesNotContainControlChars,
    DoesNotContainLinebreak,
    DoesNotContainTex,
    DoesNotContainUnnecessaryEscape,
    DoesNotStartWithLowercase,
    NoBoundaryWhitespace,
    NoExcessiveCapitals,
    NoExtraWhitespace,
    NoHtmlElements,
    NoUnapprovedLongCapsWords,
    NoUnnecessarySpaceInParens,
    NoUtf8DecodingErrors,
    NotEmpty,
    NotTooLong,
    NotTooShort,
)


def inputs(title: str) -> Inputs:
    return Inputs(metadata=Metadata(title=title))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title", **kwargs)


class TestNotEmpty:
    check = make(NotEmpty)

    def test_pass(self):
        assert self.check.run(inputs("hello")).passed

    def test_pass_on_failure_policy_warn(self):
        assert self.check.run(inputs("hello")).check_config["on_failure_policy"] == OnFailurePolicy.WARN

    def test_fail_empty(self):
        result = self.check.run(inputs(""))
        assert not result.passed
        assert result.message

    def test_fail_on_failure_policy_warn(self):
        assert self.check.run(inputs("")).check_config["on_failure_policy"] == OnFailurePolicy.WARN

    def test_fail_missing_field(self):
        with pytest.raises(MissingDataError):
            self.check.run(Inputs(metadata=Metadata(title=None)))

    def test_fail_missing_data(self):
        with pytest.raises(MissingDataError):
            self.check.run(Inputs())


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

    def test_pass_empty(self):
        assert self.check.run(inputs("")).passed


class TestNoUnapprovedLongCapsWords:
    check = make(NoUnapprovedLongCapsWords)

    def test_pass_normal(self):
        assert self.check.run(inputs("A fine title")).passed

    def test_pass_known_words(self):
        assert self.check.run(inputs("The is a title with known long words capitalized AMANDA CHANDRA")).passed

    def test_pass_single_unapproved(self):
        assert self.check.run(inputs("This is a title WITH ONE LONG WORD CAPITALIZED")).passed

    def test_fail_two_unapproved(self):
        result = self.check.run(inputs("title with unknown long words UNIQUEWORD THISISATEST"))
        assert not result.passed
        assert len(result.offsets) == 2

    def test_pass_digit_strings(self):
        assert self.check.run(inputs("The is a title with 12345678 and 987654321 words not capitalized")).passed

    def test_pass_short_caps(self):
        assert self.check.run(inputs("The ISBN and DOI are valid")).passed


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

    def test_pass_regular_backslash(self):
        assert self.check.run(inputs("a \\command title")).passed


class TestDoesNotContainTex:
    check = make(DoesNotContainTex)

    def test_pass(self):
        assert self.check.run(inputs("A clean title")).passed

    def test_fail_href(self):
        assert not self.check.run(inputs("contains \\href{url} text")).passed

    def test_fail_url(self):
        assert not self.check.run(inputs("contains \\url{http://example.com}")).passed

    def test_fail_case_insensitive(self):
        assert not self.check.run(inputs("contains \\HREF{url} text")).passed


class TestNoBoundaryWhitespace:
    check = make(NoBoundaryWhitespace)

    def test_pass(self):
        assert self.check.run(inputs("A title")).passed

    def test_fail_leading_space(self):
        result = self.check.run(inputs("  A title with leading space"))
        assert not result.passed

    def test_fail_leading_tab(self):
        assert not self.check.run(inputs("\tA title")).passed

    def test_fail_trailing_space(self):
        assert not self.check.run(inputs("A title with trailing space ")).passed

    def test_fail_trailing_tab(self):
        assert not self.check.run(inputs("A title\t")).passed


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
