from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    NotEmpty,
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
    id = 0
    version = "1.0.0"
    description = "The metadata title field is valid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, title: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(title=title)))

    _checks = (
        NotEmpty(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="title"),
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
