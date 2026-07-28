"""Journal reference metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooShort,
    NotTooLong,
    DoesNotContainAppear,
    DoesNotContainUrl,
    DoesNotContainDoi,
    DoesNotContainBareDoi,
    DoesNotContainAccepted,
    DoesNotContainInPress,
    DoesNotContainRightarrowMacro,
    DoesNotContainSubmitted,
    DoesNotContainTexHardSpaceAfterPeriod,
    DoesNotContainToBePublished,
    DoesNotContainBibtex,
    DoesNotEndWithTrailingPeriod,
    JournalRefContainsValidYear,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NotTooManyLines,
    NoUnnecessarySpaceInParens,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
    UrlDoesNotEndWithPeriod,
)


class JournalRefIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata journal_ref field."""

    name = "journal_ref_is_valid"
    display_name = "Journal Reference Is Valid"
    id = 600
    version = "1.0.0"
    description = "The metadata journal_ref field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Journal reference is invalid."

    required_data = {"metadata"}

    @classmethod
    def check(cls, journal_ref: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(journal_ref=journal_ref)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.journal_ref in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        NotTooShort(5, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NotTooLong(240, on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainBareDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainAccepted(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotContainSubmitted(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotContainInPress(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotContainAppear(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotContainToBePublished(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        JournalRefContainsValidYear(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotContainBibtex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainRightarrowMacro(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"
        ),
        DoesNotContainTexHardSpaceAfterPeriod(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"
        ),
        UrlDoesNotEndWithPeriod(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        DoesNotEndWithTrailingPeriod(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        NotTooManyLines(3, on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="journal_ref"),
    )
