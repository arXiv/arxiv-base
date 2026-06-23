"""Comments metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
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
    display_name = "Comments Are Valid"
    id = 530
    version = "1.0.0"
    description = "The metadata comments field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Comments are invalid."

    required_data = {"metadata"}

    @classmethod
    def check(cls, comments: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(comments=comments)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.comments in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

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
