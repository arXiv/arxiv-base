"""Generic punctuation checks."""

from qa.checks.base import BaseGenericPatternCheck


class DoesNotEndWithPunctuation(BaseGenericPatternCheck):
    name = "does_not_end_with_punctuation"
    display_name = "Does Not End With Punctuation"
    id = 10029
    version = "1.0.0"
    description = "The value does not end with punctuation."
    failure_message = "Ends with punctuation."

    _pattern = r"(?i)[!$%^&(_=`:;,.?-]$"


class DoesNotEndWithPeriod(BaseGenericPatternCheck):
    name = "does_not_end_with_period"
    display_name = "Does Not End With Period"
    id = 10058
    version = "1.0.0"
    description = "The value does not end with a period."
    failure_message = "Ends with a period."

    _pattern = r"\.$"


class DoesNotContainSemicolon(BaseGenericPatternCheck):
    name = "does_not_contain_semicolon"
    display_name = "Does Not Contain Semicolon"
    id = 10022
    version = "1.0.0"
    description = "The value does not contain a semicolon."
    failure_message = "Contains one or more semicolons."

    _pattern = r";"


class DoesNotContainComma(BaseGenericPatternCheck):
    name = "does_not_contain_comma"
    display_name = "Does Not Contain Comma"
    id = 10071
    version = "1.0.0"
    description = "The value does not contain a comma."
    failure_message = "Contains one or more commas."

    _pattern = r","
