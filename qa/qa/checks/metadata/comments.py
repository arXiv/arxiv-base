"""Comments metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooLong,
    DoesNotContainLinebreak,
    NoExcessiveCapitals,
    DoesNotContainUnnecessaryEscape,
    DoesNotContainTex,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    AllBracketsBalanced,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class CommentsAreValid(BaseAggregateCheck):
    """Aggregate check for the metadata comments field."""

    name = "comments_are_valid"
    id = 6
    version = "1.0.0"
    description = "The metadata comments field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Comments are invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, comments: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(comments=comments)))

    def _run(self, inputs: Inputs) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if not inputs.metadata.comments:  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(inputs)

    _checks = (
        NotTooLong(10000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        DoesNotContainTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
    )
