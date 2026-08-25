"""Generic structural integrity checks (brackets, HTML)."""

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
