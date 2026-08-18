"""Generic content checks: required and forbidden terms."""

from qa.checks.base import BaseGenericPatternCheck, BaseGenericCheck
from qa.checks.models import QaDataRegistry, Result
from ftlangdetect import detect


class IsEnglish(BaseGenericCheck):
    name = "is_english"
    display_name = "Is English"
    id = 10070
    version = "1.0.0"
    description = "The value must contain English text."
    failure_message = "Likely not in English."

    min_chars = 5

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        if len(v) < self.min_chars:
            return self._result(passed=True)

        result = detect(v)

        # TODO: language ID is sometimes not accurate. Use score?
        if result and result.get("lang") == "en":
            return self._result(passed=True)
        else:
            return self._result(passed=False, message=self.failure_message)


class ContainsALetterAndADigit(BaseGenericPatternCheck):
    name = "contains_a_letter_and_a_digit"
    display_name = "Contains A Letter And A Digit"
    id = 10067
    version = "1.0.0"
    description = "The value contains at least one letter and at least one digit."
    failure_message = "Missing at least one letter and one digit."

    _pattern = r"^[^A-Za-z]*$|^[^0-9]*$"


class ContainsAValidYear(BaseGenericPatternCheck):
    name = "contains_a_valid_year"
    display_name = "Contains A Valid Year"
    id = 10069
    version = "1.0.0"
    description = "The value contains a valid 4-digit year (19xx or 20xx)."
    failure_message = "Missing a valid year."

    _pattern = r"^(?:(?!\b(?:19|20)\d{2}\b)[\s\S])*$"


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


class DoesNotContainEtAl(BaseGenericPatternCheck):
    name = "does_not_contain_et_al"
    display_name = "Does Not Contain Et Al"
    id = 10059
    version = "1.0.0"
    description = "The value does not contain any form of the abbreviation 'et al.'."
    failure_message = "Contains 'et al.'."

    _pattern = r"(?i)\bet\.?\s*al\.?\b"


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
    failure_message = "Contains the word 'DOI'."

    _pattern = r"(?i)doi"


class DoesNotContainBareDoi(BaseGenericPatternCheck):
    name = "does_not_contain_bare_doi"
    display_name = "Does Not Contain Bare DOI"
    id = 10040
    version = "1.0.0"
    description = "The value does not contain a bare DOI number (e.g. 10.1234/abc)."
    failure_message = "Contains a DOI."

    _pattern = r"[0-9]+(\.[0-9]+)*/.*"
