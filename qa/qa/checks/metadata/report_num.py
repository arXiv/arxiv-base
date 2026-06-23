"""Report number metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooShort,
    NotTooLong,
    DoesNotContainUrl,
    DoesNotContainDoi,
    ContainsLetters,
    ContainsDigits,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class ReportNumIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata report_num field."""

    name = "report_num_is_valid"
    display_name = "Report Number Is Valid"
    id = 550
    version = "1.0.0"
    description = "The metadata report_num field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Report number is invalid."

    required_data = {"metadata"}

    @classmethod
    def check(cls, report_num: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(report_num=report_num)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.report_num in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        NotTooShort(4, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        NotTooLong(2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        ContainsLetters(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        ContainsDigits(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
    )
