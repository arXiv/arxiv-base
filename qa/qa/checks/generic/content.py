"""Generic content checks: required and forbidden terms."""

import re

from qa.checks.base import BaseGenericPatternCheck, BaseGenericCheck
from qa.checks.models import Result, Offset, QaDataRegistry


class ContainsALetterAndADigit(BaseGenericPatternCheck):
    name = "contains_a_letter_and_a_digit"
    display_name = "Contains A Letter And A Digit"
    id = 10067
    version = "1.0.0"
    description = "The value contains at least one letter and at least one digit."
    failure_message = "Missing a letter or a digit."

    _pattern = r"^[^A-Za-z]*$|^[^0-9]*$"


class ContainsAValidYear(BaseGenericCheck):
    name = "contains_a_valid_year"
    display_name = "Contains A Valid Year"
    id = 10069
    version = "1.0.0"
    description = "The value contains a valid 4-digit year (19xx or 20xx)."
    failure_message = "Does not contain a valid year."

    _year_pattern = re.compile(r"\b(?:19|20)\d{2}\b")

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        if self._year_pattern.search(v):
            return self._result(passed=True)

        return self._result(
            passed=False,
            message=self.failure_message,
            offsets=[Offset(start=0, end=len(v))],
        )


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


class DoesNotContainEtAlWithPeriod(BaseGenericPatternCheck):
    name = "does_not_contain_et_al_with_period"
    display_name = "Does Not Contain Et Al With Period"
    id = 10059
    version = "1.0.0"
    description = "The value does not contain the malformed abbreviation 'et. al.' (a period should not follow 'et')."
    failure_message = "Contains 'et. al.'."

    _pattern = r"(?i)\bet\.\s*al\b"


class DoesNotContainPendingPublicationStatus(BaseGenericPatternCheck):
    name = "does_not_contain_pending_publication_status"
    display_name = "Does Not Contain Pending Publication Status"
    id = 10068
    version = "1.0.0"
    description = (
        "The value does not contain 'submit', 'in press', 'appear', 'accept', or 'to be publ' "
        "(which belong in Comments instead)."
    )
    failure_message = "Contains pending-publication language that belongs in Comments instead."

    _pattern = r"(?i)submit|in press|appear|accept|to be publ"
