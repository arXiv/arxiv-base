"""Generic text checks."""

from qa.checks.models import Result, Offset, OnFailurePolicy, Inputs
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


class NoUnapprovedLongCapsWords(BaseGenericPatternCheck):
    name = "no_unapproved_long_caps_words"
    id = 12  # NOTE: new
    version = "1.0.0"
    description = "The value does not contain two or more unapproved all caps words that are 6 or more characters long."
    failure_message = "Contains unapproved long caps words."

    _pattern = r"\b[A-Z][A-Z-]*[A-Z]\b"

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)

        offsets = []

        for match in self._compiled_pattern.finditer(v):
            word = match.group()
            if len(word) >= 6 and word not in KNOWN_WORDS_IN_ALL_CAPS:
                offsets.append(Offset(start=match.start(), end=match.end()))

        if len(offsets) < 2:
            return self._result(passed=True)
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
        on_failure_policy: OnFailurePolicy,
        data: str,
        field: str,
    ) -> None:
        super().__init__(on_failure_policy=on_failure_policy, data=data, field=field)
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
        on_failure_policy: OnFailurePolicy,
        data: str,
        field: str,
    ) -> None:
        super().__init__(on_failure_policy=on_failure_policy, data=data, field=field)
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


class DoesNotContainControlCharsAllowNewlines(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars_allow_newlines"
    id = 18
    version = "1.0.0"
    description = "The value does not contain control characters, but newlines (\\n) are permitted."
    failure_message = "Contains control characters."

    _pattern = r"[\u0000-\u0009\u000b-\u001f]+"


class NoUtf8DecodingErrors(BaseGenericPatternCheck):
    name = "no_utf8_decoding_errors"
    id = 14
    version = "1.0.0"
    description = "The value does not contain malformed Unicode sequences."
    failure_message = "Bad Unicode encoding."

    _pattern = r"[\u00c0-\u00ff][\u0080-\u00bf]+"


# was BAD_CHARACTERS
class NoAnnotationSymbols(BaseGenericPatternCheck):
    name = "no_annotation_symbols"
    id = 15
    version = "1.0.0"
    description = "The value does not contain invalid characters such as *, #, ^, or @."
    failure_message = "Unusual character detected."

    _pattern = r"\*|#|[^\\]\^|@"


class DoesNotContainAnonymous(BaseGenericPatternCheck):
    name = "does_not_contain_anonymous"
    id = 19
    version = "1.0.0"
    description = "The value does not contain the word 'anonymous'."
    failure_message = "Contains 'anonymous'."

    _pattern = r"(?i)anonymous"


class DoesNotContainCorresponding(BaseGenericPatternCheck):
    name = "does_not_contain_corresponding"
    id = 20
    version = "1.0.0"
    description = "The value does not contain the word 'corresponding'."
    failure_message = "Contains 'corresponding'."

    _pattern = r"(?i)corresponding"


class DoesNotContainTexDagger(BaseGenericPatternCheck):
    name = "does_not_contain_tex_dagger"
    id = 21
    version = "1.0.0"
    description = "The value does not contain TeX dagger symbols (\\dag, \\ddag, etc.)."
    failure_message = "Contains a dagger symbol."

    _pattern = r"\\dag|\\ddag|\\textdag|\\textddag"


class DoesNotBeginWithAuthor(BaseGenericPatternCheck):
    name = "does_not_begin_with_author"
    id = 4
    version = "1.0.0"
    description = "The value does not begin with the prefix 'author' or 'authors'."
    failure_message = "Begins with 'author'."

    _pattern = r"(?i)^authors?:?\b"


class DoesNotContainTildeAsHardSpace(BaseGenericPatternCheck):
    name = "does_not_contain_tilde_as_hard_space"
    id = 32
    version = "1.0.0"
    description = "The value does not contain an unescaped tilde used as a hard space."
    failure_message = "Tilde as hard space."

    _pattern = r"[^\\]~"


class DoesNotBeginWithAbstract(BaseGenericPatternCheck):
    name = "does_not_begin_with_abstract"
    id = 5
    version = "1.0.0"
    description = "The value does not begin with the literal prefix 'abstract'."
    failure_message = "Begins with 'abstract'."

    _pattern = r"(?i)^abstract\b"


class DoesNotContainTexBeginEnv(BaseGenericPatternCheck):
    name = "does_not_contain_tex_begin_env"
    id = 17
    version = "1.0.0"
    description = "The value does not contain a tex begin command that is not followed by a curly brace."
    failure_message = "Contains TeX."

    _pattern = r"(?i)\\begin[^{]"


class DoesNotEndWithPunctuation(BaseGenericPatternCheck):
    name = "does_not_end_with_punctuation"
    id = 29
    version = "1.0.0"
    description = "The value does not end with punctuation (trailing 'et al.' is permitted)."
    failure_message = "Ends with punctuation."

    _pattern = r"(?i)(?<!et al)[!$%^&(_=`:;,.?-]$"


class DoesNotContainUrl(BaseGenericPatternCheck):
    name = "does_not_contain_url"
    id = 39
    version = "1.0.0"
    description = "The value does not contain a URL."
    failure_message = "Contains a URL."

    _pattern = r"(?i)https?:"


class DoesNotContainDoi(BaseGenericPatternCheck):
    name = "does_not_contain_doi"
    id = 45
    version = "1.0.0"
    description = "The value does not contain a DOI."
    failure_message = "Contains a DOI."

    _pattern = r"(?i)doi"


class DoesNotContainBareDoi(BaseGenericPatternCheck):
    name = "does_not_contain_bare_doi"
    id = 40
    version = "1.0.0"
    description = "The value does not contain a bare DOI number (e.g. 10.1234/abc)."
    failure_message = "Contains a DOI."

    _pattern = r"(?i)^[0-9][0-9].[0-9]+/[^ ]*$"


class ContainsLetters(BaseGenericPatternCheck):
    name = "contains_letters"
    id = 38
    version = "1.0.0"
    description = "The value contains at least one letter."
    failure_message = "No letters found."

    _pattern = r"^[^A-Za-z]*$"


class ContainsDigits(BaseGenericPatternCheck):
    name = "contains_digits"
    id = 37
    version = "1.0.0"
    description = "The value contains at least one digit."
    failure_message = "No digits found."

    _pattern = r"^[^0-9]*$"


class DoesNotContainAccepted(BaseGenericPatternCheck):
    name = "does_not_contain_accepted"
    id = 41
    version = "1.0.0"
    description = "The value does not contain the word 'accepted'."
    failure_message = "Contains 'accepted'."

    _pattern = r"(?i)accepted"


class DoesNotContainSubmitted(BaseGenericPatternCheck):
    name = "does_not_contain_submitted"
    id = 42
    version = "1.0.0"
    description = "The value does not contain the word 'submitted'."
    failure_message = "Contains 'submitted'."

    _pattern = r"(?i)submitted"


class DoesNotContainBibtex(BaseGenericPatternCheck):
    name = "does_not_contain_bibtex"
    id = 44
    version = "1.0.0"
    description = "The value does not contain BibTeX field assignments."
    failure_message = "Contains bibtex."

    _pattern = r"(?i)(title|booktitle|inproceedings)="
