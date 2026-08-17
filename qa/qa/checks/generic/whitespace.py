"""Generic whitespace checks."""

from qa.checks.base import BaseGenericPatternCheck


class NoExtraWhitespace(BaseGenericPatternCheck):
    name = "no_extra_whitespace"
    display_name = "No Extra Whitespace"
    id = 10025
    version = "1.0.0"
    description = "The value does not contain multiple consecutive spaces, trailing whitespace before a newline, or irregular comma spacing."
    failure_message = "Excessive whitespace: multiple consecutive spaces, trailing whitespace before a newline, or irregular comma spacing."

    _pattern = r"\s+\n|[^ \t\n,][ \t][ \t]+[^ \t\n,]|\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+"


class NoUnnecessarySpaceInParens(BaseGenericPatternCheck):
    name = "no_unnecessary_space_in_parens"
    display_name = "No Unnecessary Space in Parens"
    id = 10033
    version = "1.0.0"
    description = "The value does not contain leading or trailing spaces immediately inside parentheses."
    failure_message = "Unnecessary space inside parentheses."

    _pattern = r"\(\s|\s\)"


class DoesNotContainSpaceAfterOpenParen(BaseGenericPatternCheck):
    name = "does_not_contain_space_after_open_paren"
    display_name = "Does Not Contain Space After Open Paren"
    id = 10060
    version = "1.0.0"
    description = "The value does not contain a space immediately after an opening parenthesis."
    failure_message = "Space after opening parenthesis."

    _pattern = r"\(\s"


class DoesNotContainSpaceBeforeComma(BaseGenericPatternCheck):
    name = "does_not_contain_space_before_comma"
    display_name = "Does Not Contain Space Before Comma"
    id = 10061
    version = "1.0.0"
    description = "The value does not contain a space immediately before a comma."
    failure_message = "Space before comma."

    _pattern = r"\s,"


class DoesNotContainUnspacedComma(BaseGenericPatternCheck):
    name = "does_not_contain_unspaced_comma"
    display_name = "Does Not Contain Unspaced Comma"
    id = 10062
    version = "1.0.0"
    description = "The value does not contain a comma with no space on either side."
    failure_message = "Missing space after comma."

    _pattern = r"[A-Za-z],[A-Za-z]"
