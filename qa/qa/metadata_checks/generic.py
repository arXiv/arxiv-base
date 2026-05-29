"""Generic text checks."""

import re
from typing import Any

from qa.metadata_checks import models
from qa.metadata_checks.base import BaseGenericCheck, BaseGenericPatternCheck
from qa.metadata_checks.models import Offset

from qa.checks.constants.all_caps_words import KNOWN_WORDS_IN_ALL_CAPS


class DoesNotStartWithLowercase(BaseGenericCheck):
    name = "does_not_start_with_lowercase"
    id = 8
    version = "1.0.0"
    description = "The value does not start with a lowercase letter."

    failure_message = "Begins with a lowercase letter."

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, None)

        if v and v[0].isupper():
            return self._result(
                passed=True,
            )
        else:
            return self._result(
                passed=False,
                message=self.failure_message,
                offsets=[Offset(start=0, end=min(1, len(v)), excerpt=v[:1])],
            )


class NoExcessiveCapitals(BaseGenericCheck):
    name = "no_excessive_capitals"
    id = 7
    version = "1.0.0"
    description = "The value does not contain excessive capitals."

    failure_message = "Likely excessive capitalization."

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, None)

        num_caps = sum([c.isupper() for c in v])
        num_lower = sum([c.islower() for c in v])

        if v and num_caps <= num_lower * 2 + 7:
            return self._result(passed=True)
        else:
            return self._result(passed=False, message=self.failure_message)


class NoUnapprovedLongCapsWords(BaseGenericCheck):
    name = "no_unapproved_long_caps_words"
    id = 12  # NOTE: new
    version = "1.0.0"
    description = "The value does not contain two or more unapproved all caps words that are 6 or more characters long."

    failure_message = "Contains unapproved long caps words."

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, None)
        violating_words = []
        offsets = []

        pattern = re.compile(r"\b[A-Z][A-Z-]*[A-Z]\b")

        for match in pattern.finditer(v):
            word = match.group()

            if len(word) >= 6 and word not in KNOWN_WORDS_IN_ALL_CAPS:
                violating_words.append(word)
                offsets.append(models.Offset(start=match.start(), end=match.end()))

        if len(violating_words) < 2:
            return self._result(passed=True)
        else:
            return self._result(
                passed=False,
                message=self.failure_message,
                offsets=offsets,
            )


class NoTrailingWhitespace(BaseGenericPatternCheck):
    name = "no_trailing_whitespace"
    id = 17
    version = "1.0.0"
    description = "The value does not contain trailing whitespace."

    failure_message = "Trailing whitespace."

    _pattern = r"\s$"


class NoLeadingWhitespace(BaseGenericPatternCheck):
    name = "no_leading_whitespace"
    id = 16
    version = "1.0.0"
    description = "The value does not contain leading whitespace."

    failure_message = "Leading whitespace."

    _pattern = r"^\s"


# was EXTRA_WHITESPACE
class NoRedundantOrSpacedCommas(BaseGenericPatternCheck):
    name = "no_redundant_or_spaced_commas"
    id = 25
    version = "1.0.0"
    description = (
        "The value does not contain consecutive commas, or whitespace preceding commas."
    )

    failure_message = "Redundant or spaced commas."

    _pattern = r"(?i)\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+"


# was EXTRA_WHITESPACE_ABS
class NoExtraInternalOrTrailingSpaces(BaseGenericPatternCheck):
    name = "no_extra_internal_or_trailing_spaces"
    id = 35
    version = "1.0.0"
    description = "The value does not contain trailing spaces before a newline or multiple consecutive spaces between words."

    failure_message = (
        "Unnecessary consecutive spaces or trailing spaces before a newline."
    )

    _pattern = r"\s+\n|[^ \t\n,][ \t][ \t]+[^ \t\n,]"


class NoUnnecessarySpaceInParens(BaseGenericPatternCheck):
    name = "no_unnecessary_space_in_parens"
    id = 33
    version = "1.0"
    description = "The value does not contain leading or trailing spaces immediately inside parentheses."

    failure_message = "Unnecessary space inside parentheses."

    _pattern = r"\(\s|\s\)"


class NoHtmlElements(BaseGenericPatternCheck):
    name = "no_html_elements"
    id = 11
    version = "1.0"
    description = "The value does not contain raw HTML elements."

    failure_message = "Contains HTML."

    HTML_ELEMENTS = [
        "<p>",
        "<p ",
        "</p>",
        "<div[^a-z]",
        "</div>",
        "<br[^a-z]",
        "</br>",
        "</a>",
        "<img[^a-z]",
        "</img>",
        "<sup[^a-z]",
        "</sup>",
        "<sub[^a-z]",
        "</sub>",
        "<table[^a-z]",
        "</table>",
    ]

    _pattern = "|".join(HTML_ELEMENTS)


class AllBracketsBalanced(BaseGenericCheck):
    name = "all_brackets_balanced"
    id = 13
    version = "1.0.0"
    description = (
        "All parentheses, square brackets, and curly braces are properly closed."
    )

    failure_message = "Unbalanced brackets."

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, "")

        bracket_pairs = {"(": ")", "[": "]", "{": "}"}

        stack: list[tuple[str, int]] = []
        error_index = None

        for index, char in enumerate(v):
            if char in bracket_pairs:
                stack.append((char, index))
            elif char in ")}]":
                if stack and bracket_pairs[stack[-1][0]] == char:
                    stack.pop()  # bracket closed, remove from stack
                else:
                    error_index = index
                    break
        else:
            if stack:  # if the stack still has items, the last bracket is unclosed
                error_index = stack[-1][1]

        if not error_index:
            return self._result(passed=True)
        else:
            return self._result(
                passed=False,
                message=self.failure_message,
                offsets=[models.Offset(start=error_index, end=error_index + 1)],
            )


class NotTooLong(BaseGenericCheck):
    name = "not_too_long"
    id = 36
    version = "1.0.0"
    description = "The value does not exceed the maximum character length."

    failure_message = "Too long."

    def __init__(
        self,
        max_chars: int,
        *,
        disposition: models.Disposition,
        data_key: str,
        field: str,
    ) -> None:
        super().__init__(disposition=disposition, data_key=data_key, field=field)
        self.max_chars = max_chars

    @property
    def config(self) -> dict:
        return {**super().config, "max_chars": self.max_chars}

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, None)

        if len(v) <= self.max_chars:
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[models.Offset(start=self.max_chars, end=len(v))],
        )


class NotTooShort(BaseGenericCheck):
    name = "not_too_short"
    id = 2
    version = "1.0.0"
    description = "The value meets or exceeds the minimum character length."

    failure_message = "Too short."

    def __init__(
        self,
        min_chars: int,
        *,
        disposition: models.Disposition,
        data_key: str,
        field: str,
    ) -> None:
        super().__init__(disposition=disposition, data_key=data_key, field=field)
        self.min_chars = min_chars

    @property
    def config(self) -> dict:
        return {**super().config, "min_chars": self.min_chars}

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, None)

        if len(v) >= self.min_chars:
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[models.Offset(start=0, end=len(v))],
        )


class NotEmpty(BaseGenericCheck):
    name = "not_empty"
    id = 1
    version = "1.0.0"
    description = "The value is not an empty string."

    failure_message = "Cannot be empty."

    def _run(self, data: dict[str, Any]) -> models.Result:
        v = getattr(data[self.data_key], self.field, None)

        if v is not None and v != "":
            return self._result(passed=True)

        return self._result(passed=False, message=self.failure_message)


class DoesNotBeginWithTitle(BaseGenericPatternCheck):
    name = "does_not_begin_with_title"
    id = 3
    version = "1.0.0"
    description = "The value does not begin with the literal prefix 'title:'."

    failure_message = "Begins with 'title'."

    _pattern = r"(?i)^title:?\b"


class DoesNotContainLinebreak(BaseGenericPatternCheck):
    name = "does_not_contain_linebreak"
    id = 6
    version = "1.0.0"
    description = "The value does not contain LaTeX-style or escaped linebreaks."

    failure_message = "Contains a line break."

    _pattern = r"(?i)\\\\"


class DoesNotContainUnnecessaryEscape(BaseGenericPatternCheck):
    name = "does_not_contain_unnecessary_escape"
    id = 10
    version = "1.0.0"
    description = "The value does not contain unnecessary escape characters preceding hash or percent symbols."

    failure_message = "Contains unnecessary escape."

    _pattern = r"(?i)\\#|(?i)\\%"


class DoesNotContainTex(BaseGenericPatternCheck):
    name = "does_not_contain_tex"
    id = 9
    version = "1.0.0"
    description = "The value does not contain href or url raw TeX commands."

    failure_message = "Contains TeX."

    _pattern = r"(?i)\\href\{|(?i)\\url\{"


class DoesNotContainControlChars(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars"
    id = 26
    version = "1.0.0"
    description = "The value does not contain control characters including newlines, tabs, and backspaces."

    failure_message = "Contains control characters: newlines, tabs, or backspaces."

    _pattern = r"[\u0000-\u001f]+"


# was BAD_UNICODE_ENCODING
class NoUtf8DecodingErrors(BaseGenericPatternCheck):
    name = "no_utf8_decoding_errors"
    id = 14
    version = "1.0.0"
    description = "The value does not contain malformed Unicode sequences."

    failure_message = "Bad Unicode encoding."

    _pattern = r"[\u00c0-\u00ff][\u0080-\u00bf]+"
