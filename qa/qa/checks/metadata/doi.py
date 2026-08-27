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
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="doi"),
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
        """Normalize doi."""
        # Strip leading and trailing whitespace.
        value = value.strip()
        # Convert every control character to a space.
        value = "".join(" " if ord(c) < 0x20 else c for c in value)
        # Collapse whitespace.
        value = re.sub(r"\s+", " ", value)
        # Strip a leading "doi:", "https://doi.org/", or similar URL prefix.
        value = re.sub(r"(?i)^doi:\s*|^https?://doi\.org/|^https?://.*\.doi\.org/", "", value)
        # Remove space before a comma.
        value = re.sub(r"\s+,", ",", value)
        # Remove unnecessary space inside parentheses.
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)

        return value
