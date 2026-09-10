"""Generic structural integrity checks (brackets, HTML)."""

import bleach

from qa.checks.models import Result, Offset, QaDataRegistry
from qa.checks.base import BaseGenericCheck, BaseGenericPatternCheck


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
        "<hr[^a-z]",
        "</hr>",
        "<em[^a-z]",
        "</em>",
        "<strong[^a-z]",
        "</strong>",
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


class DoesNotContainHtmlEscapes(BaseGenericPatternCheck):
    name = "does_not_contain_html_escapes"
    display_name = "Does Not Contain HTML Escapes"
    id = 10073
    version = "1.0.0"
    description = "The value does not contain HTML escapes."
    failure_message = "Contains HTML escapes."

    _pattern = r"\&(?:[a-z]{3,4}|#x?[0-9a-f]{1,4})\;"


class DoesNotContainUnacceptableHtmlTags(BaseGenericCheck):
    name = "does_not_contain_unacceptable_html_tags"
    display_name = "Does Not Contain Unacceptable HTML Tags"
    id = 10074
    version = "1.0.0"
    description = "The value does not contain HTML tags outside of an allowed set."
    failure_message = "Contains unacceptable HTML tags."

    ALLOWED_HTML = ["br", "hr", "em", "strong", "sup", "sub", "h"]

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        cleaned = bleach.clean(v, tags=self.ALLOWED_HTML, strip=True)

        if len(v) > len(cleaned):
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)


class AllBracketsBalanced(BaseGenericCheck):
    name = "all_brackets_balanced"
    display_name = "All Brackets Balanced"
    id = 10013
    version = "1.0.0"
    description = "All parentheses, square brackets, and curly braces are properly closed."
    failure_message = "Contains unbalanced parentheses, brackets, or braces."

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


class DoesNotContainAnnotationSymbols(BaseGenericPatternCheck):
    name = "does_not_contain_annotation_symbols"
    display_name = "Does Not Contain Annotation Symbols"
    id = 10015
    version = "1.0.0"
    description = "The value does not contain annotation symbols such as *, #, ^, or @."
    failure_message = "Contains one or more annotation symbols: *, #, ^, or @."

    _pattern = r"\*|#|[^\\]\^|@"
