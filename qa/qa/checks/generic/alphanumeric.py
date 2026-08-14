"""Generic letter and digit presence checks."""

from qa.checks.base import BaseGenericPatternCheck


class ContainsALetterAndADigit(BaseGenericPatternCheck):
    name = "contains_a_letter_and_a_digit"
    display_name = "Contains A Letter And A Digit"
    id = 10067
    version = "1.0.0"
    description = "The value contains at least one letter and at least one digit."
    failure_message = "Missing a letter or a digit."

    _pattern = r"^[^A-Za-z]*$|^[^0-9]*$"
