from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, Disposition, Metadata, Result
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


class ValidTitleCheck(BaseAggregateCheck):
    """Aggregate check for the metadata title field."""

    name = "valid_title_check"
    id = 0
    version = "1.0.0"
    description = "The metadata title field is valid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, title: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(title=title)))

    _checks = (
        NotEmpty(disposition=Disposition.REJECT, data="metadata", field="title"),
        NotTooShort(5, disposition=Disposition.WARN, data="metadata", field="title"),
        NotTooLong(2000, disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotBeginWithTitle(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainLinebreak(disposition=Disposition.WARN, data="metadata", field="title"),
        NoExcessiveCapitals(disposition=Disposition.WARN, data="metadata", field="title"),
        NoUnapprovedLongCapsWords(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotStartWithLowercase(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainUnnecessaryEscape(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainTex(disposition=Disposition.WARN, data="metadata", field="title"),
        NoBoundaryWhitespace(disposition=Disposition.WARN, data="metadata", field="title"),
        NoExtraWhitespace(disposition=Disposition.WARN, data="metadata", field="title"),
        NoUnnecessarySpaceInParens(disposition=Disposition.WARN, data="metadata", field="title"),
        NoHtmlElements(disposition=Disposition.WARN, data="metadata", field="title"),
        AllBracketsBalanced(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainControlChars(disposition=Disposition.WARN, data="metadata", field="title"),
        NoUtf8DecodingErrors(disposition=Disposition.WARN, data="metadata", field="title"),
    )
