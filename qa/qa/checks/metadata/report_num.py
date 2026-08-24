"""Report number metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Result
from qa.checks import generic


class ReportNumIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata report_num field."""

    name = "report_num_is_valid"
    display_name = "Report Number Is Valid"
    id = 500
    version = "1.0.0"
    description = "The metadata report_num field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Report number is invalid."

    field = "report_num"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.report_num in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.ContainsALetterAndADigit(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="report_num"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="report_num"),
        generic.DoesNotContainSpaceBeforeComma(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="report_num"
        ),
        generic.NoUnnecessarySpaceInParens(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="report_num"
        ),
        generic.DoesNotContainControlChars(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="report_num"
        ),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="report_num"),
        generic.NotTooShort(
            min_chars=4,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="report_num",
            failure_message="Too short: must be at least 4 characters.",
        ),
        generic.NotTooLong(
            max_chars=2000,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="report_num",
            failure_message="Too long: must be 2000 characters or fewer.",
        ),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="report_num"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """Light cleanup on report number value."""
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"\s*\.[\s.]*$", "", value)
        return value
