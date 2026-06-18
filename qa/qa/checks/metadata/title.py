from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotTooShort,
    NotTooLong,
    DoesNotBeginWithTitle,
    DoesNotContainLinebreak,
    NoExcessiveCapitals,
    NoUnapprovedLongCapsWords,
    DoesNotStartWithLowercase,
    DoesNotContainUnnecessaryEscape,
    DoesNotContainTex,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
    NoHtmlElements,
    AllBracketsBalanced,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class TitleIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata title field."""

    name = "title_is_valid"
    display_name = "Title Is Valid"
    id = 500
    version = "1.0.0"
    description = "The metadata title field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Title is invalid or empty."

    required_data = {"metadata"}

    @classmethod
    def check(cls, title: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(title=title)))

    _checks = (
        NotTooShort(5, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NotTooLong(2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        DoesNotBeginWithTitle(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoUnapprovedLongCapsWords(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        DoesNotContainTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="title"),
    )
