"""Abstract metadata checks."""

import re

from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import OnFailurePolicy
from qa.checks import generic


class AbstractIsValid(BaseMetadataAggregateCheck):
    """Aggregate check for the metadata abstract field."""

    name = "abstract_is_valid"
    display_name = "Abstract Is Valid"
    id = 300
    version = "1.0.0"
    description = "The metadata abstract field is valid."
    failure_message = "Abstract is invalid."

    field = "abstract"

    _checks = (
        generic.EmptyFieldCheck(
            on_failure_policy=OnFailurePolicy.REJECT,
            data="metadata",
            field="abstract",
            failure_message="Abstract is required and cannot be empty.",
        ),
        generic.IsEnglish(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        generic.DoesNotContainUnacceptableHtmlTags(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"
        ),
        generic.NotTooShort(
            min_chars=150,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="abstract",
            failure_message="Too short: must be at least 150 characters.",
        ),
        generic.NotTooLong(
            max_chars=2000,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="abstract",
            failure_message="Too long: must be 2000 characters or fewer.",
        ),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainUnnecessaryEscape(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
        generic.DoesNotContainHrefOrUrlTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainTexBegin(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """Normalize abstract."""
        # Strip leading and trailing whitespace.
        value = value.strip()
        # Convert every control character except newline to a space.
        value = "".join(" " if ord(c) < 0x20 and c != "\n" else c for c in value)
        # Strip trailing spaces that appear right before a newline.
        value = re.sub(r"[ ]+\n", "\n", value)
        # Normalize any newline followed by some whitespace into newline + two spaces (paragraph).
        value = re.sub(r"\n\s+", "\n  ", value)
        # Convert any newline between two non-whitespace characters into a space.
        value = re.sub(r"(\S)\n(?=\S)", "\\g<1> ", value)
        # Convert multiple spaces into a single space.
        value = re.sub(r"(?<!\n)[ ]{2,}", " ", value)
        # Remove TeX return (\\) at end of a line or at the end of the abstract.
        value = re.sub(r"\s*\\\\(\n|$)", "\\g<1>", value)
        # Strip a leading "abstract:" prefix.
        value = re.sub(r"(?i)^abstract:\s*", "", value)
        # Remove space before a comma.
        value = re.sub(r"\s+,", ",", value)
        # Remove unnecessary space inside parentheses.
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)

        return value
