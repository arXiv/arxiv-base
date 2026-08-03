"""Journal reference metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic


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
    field = "journal_ref"

    @classmethod
    def check(cls, journal_ref: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(journal_ref=journal_ref)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.journal_ref in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.NotTooShort(min_chars=5, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.NotTooLong(
            max_chars=2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"
        ),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.DoesNotContainBareDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.DoesNotContainAccepted(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.DoesNotContainSubmitted(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.DoesNotContainBibtex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
        generic.NoUnnecessarySpaceInParens(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"
        ),
        generic.DoesNotContainControlChars(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"
        ),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="journal_ref"),
    )
