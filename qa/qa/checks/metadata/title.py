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
        generic.DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NotAllCaps(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainHrefOrUrlTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """Normalize title."""
        # Strip leading and trailing whitespace.
        value = value.strip()
        # Convert every control character to a space.
        value = "".join(" " if ord(c) < 0x20 else c for c in value)
        # Collapse whitespace.
        value = re.sub(r"\s+", " ", value)
        # Strip a leading "title:" prefix.
        value = re.sub(r"(?i)^title:\s*", "", value)
        # Remove space before a comma.
        value = re.sub(r"\s+,", ",", value)
        # Remove unnecessary space inside parentheses.
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)

        return value
