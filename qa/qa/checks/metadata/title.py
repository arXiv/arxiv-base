"""Title metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic


class TitleIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata title field."""

    name = "title_is_valid"
    display_name = "Title Is Valid"
    id = 100
    version = "1.0.0"
    description = "The metadata title field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Title is invalid or empty."

    required_data = {"metadata"}
    field = "title"

    @classmethod
    def check(cls, title: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(title=title)))

    _checks = (
        generic.NotTooShort(min_chars=3, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NotTooLong(max_chars=300, on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.DoesNotBeginWithTitle(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.DoesNotContainRawNewline(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoUnapprovedLongCapsWords(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
    )
