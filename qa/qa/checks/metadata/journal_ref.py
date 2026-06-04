"""Journal reference metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooShort,
    NotTooLong,
    DoesNotContainUrl,
    DoesNotContainDoi,
    DoesNotContainBareDoi,
    DoesNotContainAccepted,
    DoesNotContainSubmitted,
    DoesNotContainBibtex,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class JournalRefIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata journal_ref field."""

    name = "journal_ref_is_valid"
    id = 10
    version = "1.0.0"
    description = "The metadata journal_ref field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Journal reference is invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, journal_ref: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(journal_ref=journal_ref)))

    def _run(self, inputs: Inputs) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if not inputs.metadata.journal_ref:  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(inputs)

    _checks = (
        NotTooShort(5, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NotTooLong(2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainBareDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainAccepted(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainSubmitted(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainBibtex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
    )
