"""Generic whitespace checks."""

from qa.checks.base import BaseGenericPatternCheck


class NoExtraWhitespace(BaseGenericPatternCheck):
    name = "no_extra_whitespace"
    display_name = "No Extra Whitespace"
    id = 10025
    version = "1.0.0"
    description = "The value does not contain multiple consecutive spaces or trailing whitespace before a newline."
    failure_message = (
        "Contains excessive whitespace: multiple consecutive spaces or trailing whitespace before a newline."
    )

    _pattern = r"\s+\n|[^ \t\n,][ \t][ \t]+[^ \t\n,]"


class NoUnnecessarySpaceInParens(BaseGenericPatternCheck):
    name = "no_unnecessary_space_in_parens"
    display_name = "No Unnecessary Space in Parens"
    id = 10033
    version = "1.0.0"
    description = "The value does not contain leading or trailing spaces immediately inside parentheses."
    failure_message = "Contains unnecessary space inside parentheses."

    _pattern = r"\(\s|\s\)"


class DoesNotContainSpaceBeforeComma(BaseGenericPatternCheck):
    name = "does_not_contain_space_before_comma"
    display_name = "Does Not Contain Space Before Comma"
    id = 10061
    version = "1.0.0"
    description = "The value does not contain a space immediately before a comma."
    failure_message = "Contains space before a comma."

    _pattern = r"\s,"
