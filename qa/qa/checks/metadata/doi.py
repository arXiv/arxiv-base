"""DOI metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Result
from qa.checks import generic


class DoiIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata doi field."""

    name = "doi_is_valid"
    display_name = "DOI Is Valid"
    id = 700
    version = "1.0.0"
    description = "The metadata doi field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "DOI is invalid."

    field = "doi"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.doi in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.NotTooShort(
            min_chars=10,
            on_failure_policy=OnFailurePolicy.REJECT,
            data="metadata",
            field="doi",
            failure_message="Too short: must be at least 10 characters.",
        ),
        generic.DoesNotBeginWithDoiPrefix(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.DoesNotContainSpaceBeforeComma(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.NotTooLong(
            max_chars=50,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="doi",
            failure_message="Too long: must be 50 characters or fewer.",
        ),
        generic.DoiHasValidFormat(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """
        Collapse whitespace.
        Strip outer whitespace.
        """
        value = value.strip()
        value = re.sub(r"\s+", " ", value)

        return value
