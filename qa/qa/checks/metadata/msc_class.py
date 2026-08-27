"""MSC class metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Result
from qa.checks import generic


class MscClassIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata msc_class field."""

    name = "msc_class_is_valid"
    display_name = "MSC Class Is Valid"
    id = 800
    version = "1.0.0"
    description = "The metadata msc_class field is valid."
    failure_message = "MSC class is invalid."

    field = "msc_class"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.msc_class in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="msc_class"),
        generic.DoesNotContainSemicolon(
            on_failure_policy=OnFailurePolicy.REJECT,
            data="metadata",
            field="msc_class",
            failure_message="Separate classification keys with commas.",
        ),
        generic.NotTooLong(
            max_chars=160,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="msc_class",
            failure_message="Too long: must be 160 characters or fewer.",
        ),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """Normalize msc_class."""
        # Strip leading and trailing whitespace.
        value = value.strip()
        # Convert every control character to a space.
        value = "".join(" " if ord(c) < 0x20 else c for c in value)
        # Collapse whitespace.
        value = re.sub(r"\s+", " ", value)
        # Strip trailing periods.
        value = re.sub(r"\s*\.[\s.]*$", "", value)
        # Drop a leading "MSC classification" style prefix.
        value = re.sub(
            r"^MSC([\s:\-]{0,4}(classification|class|number))?"
            r"([\s:\-]{0,4}\(?2000\)?)?[\s:\-]*",
            "",
            value,
            flags=re.I,
        )
        # Remove unnecessary space inside parentheses.
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)

        return value
