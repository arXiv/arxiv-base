"""Journal reference metadata checks."""

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import OnFailurePolicy
from qa.checks import generic


class JournalRefIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata journal_ref field."""

    name = "journal_ref_is_valid"
    display_name = "Journal Reference Is Valid"
    id = 600
    version = "1.0.0"
    description = "The metadata journal_ref field is valid."
    failure_message = "Journal reference is invalid."

    field = "journal_ref"

    _checks = (
        generic.EmptyFieldCheck(on_failure_policy=OnFailurePolicy.IGNORE, data="metadata", field="journal_ref"),
        generic.DoesNotContainPendingPublicationStatus(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"
        ),
        generic.ContainsAValidYear(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainBareDoi(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainAccepted(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainSubmitted(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainBibtex(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.DoesNotContainSpaceBeforeComma(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"
        ),
        generic.NoUnnecessarySpaceInParens(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"
        ),
        generic.DoesNotContainControlChars(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"
        ),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        generic.NotTooShort(
            min_chars=5,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="journal_ref",
            failure_message="Too short: must be at least 5 characters.",
        ),
        generic.NotTooLong(
            max_chars=1500,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="journal_ref",
            failure_message="Too long: must be 1500 characters or fewer.",
        ),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """
        Strip outer whitespace.
        """
        value = value.strip()

        return value
