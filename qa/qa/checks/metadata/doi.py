"""DOI metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooShort,
    NotTooLong,
    DoesNotContainBadDoiPrefix,
    DoiHasValidFormat,
    DoesNotContainUrl,
    DoesNotContainDoi,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class DoiIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata doi field."""

    name = "doi_is_valid"
    display_name = "DOI Is Valid"
    id = 570
    version = "1.0.0"
    description = "The metadata doi field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "DOI is invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, doi: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(doi=doi)))

    def _run(self, inputs: Inputs) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if not inputs.metadata.doi:  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(inputs)

    _checks = (
        NotTooShort(10, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        NotTooLong(2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        DoesNotContainBadDoiPrefix(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        DoiHasValidFormat(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="doi"),
    )
