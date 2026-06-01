"""Generic text checks."""

import re

from qa.checks.models import Result, Offset, Disposition, Inputs
from qa.checks.base import BaseGenericCheck, BaseGenericPatternCheck
from qa.checks.generic.all_caps_words import KNOWN_WORDS_IN_ALL_CAPS


class DoesNotStartWithLowercase(BaseGenericPatternCheck):
    name = "does_not_start_with_lowercase"
    id = 8
    version = "1.0.0"
    description = "The value does not start with a lowercase letter."
    failure_message = "Begins with a lowercase letter."

    _pattern = r"^[a-z]"


class NoExcessiveCapitals(BaseGenericCheck):
    name = "no_excessive_capitals"
    id = 7
    version = "1.0.0"
    description = "The value does not contain excessive capitals."
    failure_message = "Likely excessive capitalization."

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

        num_caps = sum([c.isupper() for c in v])
        num_lower = sum([c.islower() for c in v])

        if num_caps <= num_lower * 2 + 7:
            return self._result(passed=True)
        else:
            return self._result(passed=False, message=self.failure_message)


class NoUnapprovedLongCapsWords(BaseGenericCheck):
    name = "no_unapproved_long_caps_words"
    id = 12  # NOTE: new
    version = "1.0.0"
    description = "The value does not contain two or more unapproved all caps words that are 6 or more characters long."
    failure_message = "Contains unapproved long caps words."

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

        violating_words = []
        offsets = []

        pattern = re.compile(r"\b[A-Z][A-Z-]*[A-Z]\b")

        for match in pattern.finditer(v):
            word = match.group()

            if len(word) >= 6 and word not in KNOWN_WORDS_IN_ALL_CAPS:
                violating_words.append(word)
                offsets.append(Offset(start=match.start(), end=match.end()))

        if len(violating_words) < 2:
            return self._result(passed=True)
        else:
            return self._result(
                passed=False,
                message=self.failure_message,
                offsets=offsets,
            )


class NoBoundaryWhitespace(BaseGenericPatternCheck):
    name = "no_boundary_whitespace"
    id = 16
    version = "1.0.0"
    description = "The value does not begin or end with whitespace."
    failure_message = "Leading or trailing whitespace."

    _pattern = r"^\s|\s$"


class NoExtraWhitespace(BaseGenericPatternCheck):
    name = "no_extra_whitespace"
    id = 25
    version = "1.0.0"
    description = "The value does not contain multiple consecutive spaces, trailing whitespace before a newline, or irregular comma spacing."
    failure_message = "Excessive or irregular whitespace."

    _pattern = r"\s+\n|[^ \t\n,][ \t][ \t]+[^ \t\n,]|\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+"


class NoUnnecessarySpaceInParens(BaseGenericPatternCheck):
    name = "no_unnecessary_space_in_parens"
    id = 33
    version = "1.0.0"
    description = "The value does not contain leading or trailing spaces immediately inside parentheses."
    failure_message = "Unnecessary space inside parentheses."

    _pattern = r"\(\s|\s\)"


class NoHtmlElements(BaseGenericPatternCheck):
    name = "no_html_elements"
    id = 11
    version = "1.0.0"
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
    description = "All parentheses, square brackets, and curly braces are properly closed."
    failure_message = "Unbalanced brackets."

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

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

        if error_index is None:
            return self._result(passed=True)
        else:
            return self._result(
                passed=False,
                message=self.failure_message,
                offsets=[Offset(start=error_index, end=error_index + 1)],
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
        disposition: Disposition,
        data: str,
        field: str,
    ) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self.max_chars = max_chars

    @property
    def config(self) -> dict:
        return {**super().config, "max_chars": self.max_chars}

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

        if len(v) <= self.max_chars:
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[Offset(start=self.max_chars, end=len(v))],
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
        disposition: Disposition,
        data: str,
        field: str,
    ) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self.min_chars = min_chars

    @property
    def config(self) -> dict:
        return {**super().config, "min_chars": self.min_chars}

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

        if len(v) >= self.min_chars:
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[Offset(start=0, end=len(v))],
        )


class NotEmpty(BaseGenericCheck):
    name = "not_empty"
    id = 1
    version = "1.0.0"
    description = "The value is not an empty string."
    failure_message = "Cannot be empty."

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

        if v != "":
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

    _pattern = r"\\#|\\%"


class DoesNotContainTex(BaseGenericPatternCheck):
    name = "does_not_contain_tex"
    id = 9
    version = "1.0.0"
    description = "The value does not contain href or url raw TeX commands."
    failure_message = "Contains TeX."

    _pattern = r"(?i)\\href\{|\\url\{"


class DoesNotContainControlChars(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars"
    id = 26
    version = "1.0.0"
    description = "The value does not contain control characters including newlines, tabs, and backspaces."
    failure_message = "Contains control characters: newlines, tabs, or backspaces."

    _pattern = r"[\u0000-\u001f]+"


class NoUtf8DecodingErrors(BaseGenericPatternCheck):
    name = "no_utf8_decoding_errors"
    id = 14
    version = "1.0.0"
    description = "The value does not contain malformed Unicode sequences."
    failure_message = "Bad Unicode encoding."

    _pattern = r"[\u00c0-\u00ff][\u0080-\u00bf]+"
