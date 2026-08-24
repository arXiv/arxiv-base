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
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Abstract is invalid or empty."

    field = "abstract"

    _checks = (
        generic.IsEnglish(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
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
        generic.DoesNotBeginWithAbstract(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainUnnecessaryEscape(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
        generic.DoesNotContainHrefOrUrlTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainTexBegin(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainSpaceBeforeComma(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainControlCharsAllowNewlines(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
    )

    @staticmethod
    def cleanup(value: str) -> str:
        """Perform some light tidying on the abstract."""
        value = value.strip()  # Remove leading or trailing spaces
        # Tidy paragraphs which should be indicated with "\n  ".
        value = re.sub(r"[ ]+\n", "\n", value)
        value = re.sub(r"\n\s+", "\n  ", value)
        # Newline with no following space is removed, so treated as just a
        # space in paragraph.
        value = re.sub(r"(\S)\n(\S)", "\\g<1> \\g<2>", value)
        # Tab->space, multiple spaces->space.
        value = re.sub(r"\t", " ", value)
        value = re.sub(r"(?<!\n)[ ]{2,}", " ", value)
        # Remove tex return (\\) at end of line or end of abstract.
        value = re.sub(r"\s*\\\\(\n|$)", "\\g<1>", value)
        # Remove lone period.
        value = re.sub(r"\n\.\n", "\n", value)
        value = re.sub(r"\n\.$", "", value)
        return value
