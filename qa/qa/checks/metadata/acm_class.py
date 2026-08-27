"""ACM class metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Result
from qa.checks import generic


class AcmClassIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata acm_class field."""

    name = "acm_class_is_valid"
    display_name = "ACM Class Is Valid"
    id = 900
    version = "1.0.0"
    description = "The metadata acm_class field is valid."
    failure_message = "ACM class is invalid."

    field = "acm_class"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.acm_class in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="acm_class"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="acm_class"),
        generic.DoesNotContainComma(
            on_failure_policy=OnFailurePolicy.REJECT,
            data="metadata",
            field="acm_class",
            failure_message="Separate classes with semicolons.",
        ),
        generic.NotTooLong(
            max_chars=160,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="acm_class",
            failure_message="Too long: must be 160 characters or fewer.",
        ),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """Normalize acm_class."""
        # Strip leading and trailing whitespace.
        value = value.strip()
        # Convert every control character to a space.
        value = "".join(" " if ord(c) < 0x20 else c for c in value)
        # Collapse whitespace.
        value = re.sub(r"\s+", " ", value)
        # Strip trailing periods.
        value = re.sub(r"\s*\.[\s.]*$", "", value)
        # Strip a leading "ACM-class:" prefix.
        value = re.sub(r"^ACM-class:\s+", "", value, flags=re.I)
        # Remove unnecessary space inside parentheses.
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)

        _value = []
        for v in value.split(";"):
            # Strip whitespace.
            # Uppercase the class code.
            # Strip trailing periods.
            v = v.strip().upper().rstrip(".")
            # Insert a dot after a leading letter (e.g. "A1" -> "A.1").
            v = re.sub(r"^([A-K])(\d)", "\\g<1>.\\g<2>", v)
            # Lowercase a trailing "M".
            v = re.sub(r"M$", "m", v)
            _value.append(v)
        value = "; ".join(_value)

        return value
