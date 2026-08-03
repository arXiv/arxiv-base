"""Comments metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic


class CommentsAreValid(BaseAggregateCheck):
    """Aggregate check for the metadata comments field."""

    name = "comments_are_valid"
    display_name = "Comments Are Valid"
    id = 400
    version = "1.0.0"
    description = "The metadata comments field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Comments are invalid."

    required_data = {"metadata"}
    field = "comments"

    @classmethod
    def check(cls, comments: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(comments=comments)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.comments in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.NotTooLong(max_chars=10000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.DoesNotContainTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
    )
