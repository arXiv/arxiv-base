from qa.metadata_checks.base import BaseAggregateCheck
from qa.metadata_checks.models import Disposition
from qa.metadata_checks.generic import (
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
    NoLeadingWhitespace,
    NoTrailingWhitespace,
    NoRedundantOrSpacedCommas,
    NoUnnecessarySpaceInParens,
    NoHtmlElements,
    AllBracketsBalanced,
    DoesNotContainControlChars,
    NoUtf8DecodingErrors,
)


class ValidTitleCheck(BaseAggregateCheck):
    """Aggregated check for the metadata title field."""

    name = "valid_title_check"
    version = "1.0.0"
    description = "The metadata title field is valid."

    required_data = {"metadata"}

    _checks = (
        NotEmpty(disposition=Disposition.REJECT, data="metadata", field="title"),
        NotTooShort(disposition=Disposition.WARN, data="metadata", field="title"),
        NotTooLong(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotBeginWithTitle(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainLinebreak(disposition=Disposition.WARN, data="metadata", field="title"),
        NoExcessiveCapitals(disposition=Disposition.WARN, data="metadata", field="title"),
        NoUnapprovedLongCapsWords(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotStartWithLowercase(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainUnnecessaryEscape(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainTex(disposition=Disposition.WARN, data="metadata", field="title"),
        NoLeadingWhitespace(disposition=Disposition.WARN, data="metadata", field="title"),
        NoTrailingWhitespace(disposition=Disposition.WARN, data="metadata", field="title"),
        NoRedundantOrSpacedCommas(disposition=Disposition.WARN, data="metadata", field="title"),
        NoUnnecessarySpaceInParens(disposition=Disposition.WARN, data="metadata", field="title"),
        NoHtmlElements(disposition=Disposition.WARN, data="metadata", field="title"),
        AllBracketsBalanced(disposition=Disposition.WARN, data="metadata", field="title"),
        DoesNotContainControlChars(disposition=Disposition.WARN, data="metadata", field="title"),
        NoUtf8DecodingErrors(disposition=Disposition.WARN, data="metadata", field="title"),
    )
