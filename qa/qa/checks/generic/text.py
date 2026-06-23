"""Generic text checks."""

from qa.checks.models import Result, Offset, OnFailurePolicy, QaDataRegistry
from qa.checks.base import BaseGenericCheck, BaseGenericPatternCheck
from qa.checks.generic.all_caps_words import KNOWN_WORDS_IN_ALL_CAPS

# Note: the ids in this file should be the metadata check id + 10000,
# to avoid collision with the check_ids previously used in the arxiv_checks table.

class DoesNotStartWithLowercase(BaseGenericPatternCheck):
    name = "does_not_start_with_lowercase"
    display_name = "Does Not Start With Lowercase"
    id = 10008
    version = "1.0.0"
    description = "The value does not start with a lowercase letter."
    failure_message = "Begins with a lowercase letter."

    _pattern = r"^[a-z]"


class NoExcessiveCapitals(BaseGenericCheck):
    name = "no_excessive_capitals"
    display_name = "No Excessive Capitals"
    id = 10007
    version = "1.0.0"
    description = "The value does not contain excessive capitals."
    failure_message = "Likely excessive capitalization."

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        num_caps = sum([c.isupper() for c in v])
        num_lower = sum([c.islower() for c in v])

        if num_caps <= num_lower * 2 + 7:
            return self._result(passed=True)
        else:
            return self._result(passed=False, message=self.failure_message)


class NoUnapprovedLongCapsWords(BaseGenericPatternCheck):
    name = "no_unapproved_long_caps_words"
    display_name = "No Unapproved Long Caps Words"
    id = 10012  # NOTE: new
    version = "1.0.0"
    description = "The value does not contain two or more unapproved all caps words that are 6 or more characters long."
    failure_message = "Contains unapproved long caps words."

    _pattern = r"\b[A-Z][A-Z-]*[A-Z]\b"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

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
    display_name = "No Boundary Whitespace"
    id = 10016
    version = "1.0.0"
    description = "The value does not begin or end with whitespace."
    failure_message = "Leading or trailing whitespace."

    _pattern = r"^\s|\s$"


class NoExtraWhitespace(BaseGenericPatternCheck):
    name = "no_extra_whitespace"
    display_name = "No Extra Whitespace"
    id = 10025
    version = "1.0.0"
    description = "The value does not contain multiple consecutive spaces, trailing whitespace before a newline, or irregular comma spacing."
    failure_message = "Excessive or irregular whitespace."

    _pattern = r"\s+\n|[^ \t\n,][ \t][ \t]+[^ \t\n,]|\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+"


class NoUnnecessarySpaceInParens(BaseGenericPatternCheck):
    name = "no_unnecessary_space_in_parens"
    display_name = "No Unnecessary Space in Parens"
    id = 10033
    version = "1.0.0"
    description = "The value does not contain leading or trailing spaces immediately inside parentheses."
    failure_message = "Unnecessary space inside parentheses."

    _pattern = r"\(\s|\s\)"


class NoHtmlElements(BaseGenericPatternCheck):
    name = "no_html_elements"
    display_name = "No HTML Elements"
    id = 10011
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
    display_name = "All Brackets Balanced"
    id = 10013
    version = "1.0.0"
    description = "All parentheses, square brackets, and curly braces are properly closed."
    failure_message = "Unbalanced brackets."

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

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
    display_name = "Not Too Long"
    id = 10036
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

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        if len(v) <= self.max_chars:
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[Offset(start=self.max_chars, end=len(v))],
        )


class NotTooShort(BaseGenericCheck):
    name = "not_too_short"
    display_name = "Not Too Short"
    id = 10002
    version = "1.0.0"
    description = "The value meets or exceeds the minimum character length."
    failure_message = "Text likely too short."

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

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        if len(v) >= self.min_chars:
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[Offset(start=0, end=len(v))],
        )


class DoesNotBeginWithTitle(BaseGenericPatternCheck):
    name = "does_not_begin_with_title"
    display_name = "Does Not Begin With Title"
    id = 10003
    version = "1.0.0"
    description = "The value does not begin with the literal prefix 'title:'."
    failure_message = "Begins with 'title'."

    _pattern = r"(?i)^title:?\b"


class DoesNotContainLinebreak(BaseGenericPatternCheck):
    name = "does_not_contain_linebreak"
    display_name = "Does Not Contain Linebreak"
    id = 10006
    version = "1.0.0"
    description = "The value does not contain LaTeX-style or escaped linebreaks."
    failure_message = "Contains a line break."

    _pattern = r"(?i)\\\\"


class DoesNotContainUnnecessaryEscape(BaseGenericPatternCheck):
    name = "does_not_contain_unnecessary_escape"
    display_name = "Does Not Contain Unnecessary Escape"
    id = 10010
    version = "1.0.0"
    description = "The value does not contain unnecessary escape characters preceding hash or percent symbols."
    failure_message = "Contains unnecessary escape."

    _pattern = r"\\#|\\%"


class DoesNotContainTex(BaseGenericPatternCheck):
    name = "does_not_contain_tex"
    display_name = "Does Not Contain TeX"
    id = 10009
    version = "1.0.0"
    description = "The value does not contain href or url raw TeX commands."
    failure_message = "Contains TeX."

    _pattern = r"(?i)\\href\{|\\url\{"


class DoesNotContainControlChars(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars"
    display_name = "Does Not Contain Control Chars"
    id = 10026
    version = "1.0.0"
    description = "The value does not contain control characters including newlines, tabs, and backspaces."
    failure_message = "Contains control characters: newlines, tabs, or backspaces."

    _pattern = r"[\u0000-\u001f]+"


class DoesNotContainControlCharsAllowNewlines(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars_allow_newlines"
    display_name = "Does Not Contain Control Chars (Allow Newlines)"
    id = 10018
    version = "1.0.0"
    description = "The value does not contain control characters, but newlines (\\n) are permitted."
    failure_message = "Contains control characters."

    _pattern = r"[\u0000-\u0009\u000b-\u001f]+"


class NoUtf8DecodingErrors(BaseGenericPatternCheck):
    name = "no_utf8_decoding_errors"
    display_name = "No UTF-8 Decoding Errors"
    id = 10014
    version = "1.0.0"
    description = "The value does not contain malformed Unicode sequences."
    failure_message = "Bad Unicode encoding."

    _pattern = r"[\u00c0-\u00ff][\u0080-\u00bf]+"


# was BAD_CHARACTERS
class NoAnnotationSymbols(BaseGenericPatternCheck):
    name = "no_annotation_symbols"
    display_name = "No Annotation Symbols"
    id = 10015
    version = "1.0.0"
    description = "The value does not contain invalid characters such as *, #, ^, or @."
    failure_message = "Unusual character detected."

    _pattern = r"\*|#|[^\\]\^|@"


class DoesNotContainAnonymous(BaseGenericPatternCheck):
    name = "does_not_contain_anonymous"
    display_name = "Does Not Contain Anonymous"
    id = 10019
    version = "1.0.0"
    description = "The value does not contain the word 'anonymous'."
    failure_message = "Contains 'anonymous'."

    _pattern = r"(?i)anonymous"


class DoesNotContainCorresponding(BaseGenericPatternCheck):
    name = "does_not_contain_corresponding"
    display_name = "Does Not Contain Corresponding"
    id = 10020
    version = "1.0.0"
    description = "The value does not contain the word 'corresponding'."
    failure_message = "Contains 'corresponding'."

    _pattern = r"(?i)corresponding"


class DoesNotContainTexDagger(BaseGenericPatternCheck):
    name = "does_not_contain_tex_dagger"
    display_name = "Does Not Contain TeX Dagger"
    id = 10021
    version = "1.0.0"
    description = "The value does not contain TeX dagger symbols (\\dag, \\ddag, etc.)."
    failure_message = "Contains a dagger symbol."

    _pattern = r"\\dag|\\ddag|\\textdag|\\textddag"


class DoesNotBeginWithAuthor(BaseGenericPatternCheck):
    name = "does_not_begin_with_author"
    display_name = "Does Not Begin With Author"
    id = 10004
    version = "1.0.0"
    description = "The value does not begin with the prefix 'author' or 'authors'."
    failure_message = "Begins with 'author'."

    _pattern = r"(?i)^authors?:?\b"


class DoesNotContainTildeAsHardSpace(BaseGenericPatternCheck):
    name = "does_not_contain_tilde_as_hard_space"
    display_name = "Does Not Contain Tilde As Hard Space"
    id = 10032
    version = "1.0.0"
    description = "The value does not contain an unescaped tilde used as a hard space."
    failure_message = "Tilde as hard space."

    _pattern = r"[^\\]~"


class DoesNotBeginWithAbstract(BaseGenericPatternCheck):
    name = "does_not_begin_with_abstract"
    display_name = "Does Not Begin With Abstract"
    id = 10005
    version = "1.0.0"
    description = "The value does not begin with the literal prefix 'abstract'."
    failure_message = "Begins with 'abstract'."

    _pattern = r"(?i)^abstract\b"


class DoesNotContainTexBeginEnv(BaseGenericPatternCheck):
    name = "does_not_contain_tex_begin_env"
    display_name = "Does Not Contain TeX Begin Env"
    id = 10017
    version = "1.0.0"
    description = "The value does not contain a tex begin command that is not followed by a curly brace."
    failure_message = "Contains TeX."

    _pattern = r"(?i)\\begin[^{]"


class DoesNotEndWithPunctuation(BaseGenericPatternCheck):
    name = "does_not_end_with_punctuation"
    display_name = "Does Not End With Punctuation"
    id = 10029
    version = "1.0.0"
    description = "The value does not end with punctuation (trailing 'et al.' is permitted)."
    failure_message = "Ends with punctuation."

    _pattern = r"(?i)(?<!et al)[!$%^&(_=`:;,.?-]$"


class DoesNotContainUrl(BaseGenericPatternCheck):
    name = "does_not_contain_url"
    display_name = "Does Not Contain URL"
    id = 10039
    version = "1.0.0"
    description = "The value does not contain a URL."
    failure_message = "Contains a URL."

    _pattern = r"(?i)https?:"


class DoesNotContainDoi(BaseGenericPatternCheck):
    name = "does_not_contain_doi"
    display_name = "Does Not Contain DOI"
    id = 10045
    version = "1.0.0"
    description = "The value does not contain the word 'DOI'."
    failure_message = "Contains 'DOI'."

    _pattern = r"(?i)doi"


class DoesNotContainBareDoi(BaseGenericPatternCheck):
    name = "does_not_contain_bare_doi"
    display_name = "Does Not Contain Bare DOI"
    id = 10040
    version = "1.0.0"
    description = "The value does not contain a bare DOI number (e.g. 10.1234/abc)."
    failure_message = "Contains a DOI."

    _pattern = r"(?i)^[0-9][0-9].[0-9]+/[^ ]*$"


class ContainsLetters(BaseGenericPatternCheck):
    name = "contains_letters"
    display_name = "Contains Letters"
    id = 10038
    version = "1.0.0"
    description = "The value contains at least one letter."
    failure_message = "No letters found."

    _pattern = r"^[^A-Za-z]*$"


class ContainsDigits(BaseGenericPatternCheck):
    name = "contains_digits"
    display_name = "Contains Digits"
    id = 10037
    version = "1.0.0"
    description = "The value contains at least one digit."
    failure_message = "No digits found."

    _pattern = r"^[^0-9]*$"


class DoesNotContainSemicolon(BaseGenericPatternCheck):  # TODO remove?
    name = "does_not_contain_semicolon"
    display_name = "Does Not Contain Semicolon"
    id = 10022
    version = "1.0.0"
    description = "The value does not contain a semicolon."
    failure_message = "Contains semicolon(s) - use ',' or 'and' to separate authors."

    _pattern = r";"


class DoesNotContainAccepted(BaseGenericPatternCheck):
    name = "does_not_contain_accepted"
    display_name = "Does Not Contain Accepted"
    id = 10041
    version = "1.0.0"
    description = "The value does not contain the word 'accepted'."
    failure_message = "Contains 'accepted'."

    _pattern = r"(?i)accepted"


class DoesNotContainSubmitted(BaseGenericPatternCheck):
    name = "does_not_contain_submitted"
    display_name = "Does Not Contain Submitted"
    id = 10042
    version = "1.0.0"
    description = "The value does not contain the word 'submitted'."
    failure_message = "Contains 'submitted'."

    _pattern = r"(?i)submitted"


class DoesNotContainBibtex(BaseGenericPatternCheck):
    name = "does_not_contain_bibtex"
    display_name = "Does Not Contain BibTeX"
    id = 10044
    version = "1.0.0"
    description = "The value does not contain BibTeX field assignments."
    failure_message = "Contains bibtex."

    _pattern = r"(?i)(title|booktitle|inproceedings)="


class DoesNotContainBadDoiPrefix(BaseGenericPatternCheck):
    name = "does_not_contain_bad_doi_prefix"
    display_name = "Does Not Contain Bad DOI Prefix"
    id = 10047
    version = "1.0.0"
    description = "The value does not begin with 'doi:', 'https://doi.org/', or similar URL prefixes."
    failure_message = "Contains unnecessary prefix."

    _pattern = r"(?i)^doi:|^https?://doi\.org/|^https?://.*\.doi\.org/"


class DoiHasValidFormat(BaseGenericPatternCheck):
    name = "doi_has_valid_format"
    display_name = "DOI Has Valid Format"
    id = 10050
    version = "1.0.0"
    description = "Each space-separated DOI in the value matches the expected DOI format."
    failure_message = "Invaleeid DOI."

    _pattern = r"(?i)^(?![0-9][0-9]*\.[0-9][0-9]*/[A-Za-z0-9():;._/-]*$)"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)
        offsets = []
        start = 0
        for doi in v.split():
            idx = v.index(doi, start)
            end = idx + len(doi)
            if self._compiled_pattern.match(doi):
                offsets.append(Offset(start=idx, end=end))
            start = end
        if offsets:
            return self._result(passed=False, message=self.failure_message, offsets=offsets)
        return self._result(passed=True)
