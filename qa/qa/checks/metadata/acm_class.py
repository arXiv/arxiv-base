"""ACM class metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooLong,
    DoesNotContainUrl,
    DoesNotContainDoi,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class AcmClassIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata acm_class field."""

    name = "acm_class_is_valid"
    display_name = "ACM Class Is Valid"
    id = 590
    version = "1.0.0"
    description = "The metadata acm_class field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "ACM class is invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, acm_class: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(acm_class=acm_class)))

    def _run(self, inputs: Inputs) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if not inputs.metadata.acm_class:  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(inputs)

    _checks = (
        NotTooLong(1000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
    )
