"""Comments metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Result
from qa.checks import generic


class CommentsAreValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata comments field."""

    name = "comments_are_valid"
    display_name = "Comments Are Valid"
    id = 400
    version = "1.0.0"
    description = "The metadata comments field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Comments are invalid."

    field = "comments"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.comments in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.NotTooLong(
            max_chars=1000,
            on_failure_policy=OnFailurePolicy.REJECT,
            data="metadata",
            field="comments",
            failure_message="Too long: must be 1000 characters or fewer.",
        ),
        generic.DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="comments"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="comments"),
        generic.NotAllCaps(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="comments"),
        generic.DoesNotContainUnnecessaryEscape(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"
        ),
        generic.DoesNotContainHrefOrUrlTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.DoesNotContainSpaceBeforeComma(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"
        ),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="comments"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """
        Collapse whitespace.
        Strip outer whitespace.
        Strip trailing periods.
        """
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"\s*\.[\s.]*$", "", value)

        return value
