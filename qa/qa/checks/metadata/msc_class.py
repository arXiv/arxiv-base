"""MSC class metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooLong,
    DoesNotContainUrl,
    DoesNotContainDoi,
    DoesNotContainSemicolon,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class MscClassIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata msc_class field."""

    name = "msc_class_is_valid"
    display_name = "MSC Class Is Valid"
    id = 580
    version = "1.0.0"
    description = "The metadata msc_class field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "MSC class is invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, msc_class: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(msc_class=msc_class)))

    def _run(self, inputs: Inputs) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if not inputs.metadata.msc_class:  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(inputs)

    _checks = (
        NotTooLong(1000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        DoesNotContainSemicolon(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"
        ),  # TODO remove?
    )
