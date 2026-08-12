"""Generic letter and digit presence checks."""

from qa.checks.base import BaseGenericPatternCheck


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
