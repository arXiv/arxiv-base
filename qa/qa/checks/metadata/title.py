"""Title metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import OnFailurePolicy
from qa.checks import generic


class TitleIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata title field."""

    name = "title_is_valid"
    display_name = "Title Is Valid"
    id = 100
    version = "1.0.0"
    description = "The metadata title field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Title is invalid or empty."

    field = "title"

    _checks = (
        generic.NotTooShort(
            min_chars=3,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="title",
            failure_message="Too short: must be at least 3 characters.",
        ),
        generic.NotTooLong(
            max_chars=300,
            on_failure_policy=OnFailurePolicy.REJECT,
            data="metadata",
            field="title",
            failure_message="Too long: must be 300 characters or fewer.",
        ),
        generic.DoesNotBeginWithTitle(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.DoesNotContainRawNewline(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NotAllCaps(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainHrefOrUrlTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainSpaceBeforeComma(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """
        Collapse whitespace.
        Strip outer whitespace.
        """
        value = re.sub(r"\s+", " ", value).strip()  # Single spaces only.

        return value
