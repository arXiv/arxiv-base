"""Author metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, Disposition, Metadata, Result
from qa.checks.generic.text import (
    AllBracketsBalanced,
    DoesNotBeginWithAuthor,
    DoesNotContainAnonymous,
    DoesNotContainCorresponding,
    DoesNotContainControlChars,
    DoesNotContainLinebreak,
    DoesNotContainTexDagger,
    DoesNotContainTildeAsHardSpace,
    DoesNotEndWithPunctuation,
    NoBadCharacters,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoHtmlElements,
    NoUnnecessarySpaceInParens,
    NoUtf8DecodingErrors,
    NotEmpty,
    NotTooLong,
    NotTooShort,
)
from qa.checks.generic.author_name import (
    AuthorNamesDoNotContainAffiliation,
    AuthorNamesDoNotContainBrackets,
    AuthorNamesDoNotContainNumbers,
    AuthorNamesDoNotContainSemicolon,
    AuthorsDoNotContainLlmAuthor,
    AuthorsDoNotContainLoneSurname,
)


class ValidAuthorsCheck(BaseAggregateCheck):
    """Aggregate check for the metadata authors field."""

    name = "valid_authors_check"
    id = 4
    version = "1.0.0"
    description = "The metadata authors field is valid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, authors: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(authors=authors)))

    _checks = (
        NotEmpty(disposition=Disposition.REJECT, data="metadata", field="authors"),
        NotTooShort(4, disposition=Disposition.WARN, data="metadata", field="authors"),
        NotTooLong(10000, disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotContainLinebreak(disposition=Disposition.WARN, data="metadata", field="authors"),
        NoBadCharacters(disposition=Disposition.WARN, data="metadata", field="authors"),
        NoBoundaryWhitespace(disposition=Disposition.WARN, data="metadata", field="authors"),
        NoExtraWhitespace(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotContainAnonymous(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotContainCorresponding(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotContainTexDagger(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotBeginWithAuthor(disposition=Disposition.WARN, data="metadata", field="authors"),
        NoHtmlElements(disposition=Disposition.WARN, data="metadata", field="authors"),
        AllBracketsBalanced(disposition=Disposition.WARN, data="metadata", field="authors"),
        NoUnnecessarySpaceInParens(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotContainTildeAsHardSpace(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotEndWithPunctuation(disposition=Disposition.WARN, data="metadata", field="authors"),
        DoesNotContainControlChars(disposition=Disposition.WARN, data="metadata", field="authors"),
        NoUtf8DecodingErrors(disposition=Disposition.WARN, data="metadata", field="authors"),
        AuthorsDoNotContainLoneSurname(disposition=Disposition.WARN, data="metadata", field="authors"),
        AuthorsDoNotContainLlmAuthor(disposition=Disposition.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainSemicolon(disposition=Disposition.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainBrackets(disposition=Disposition.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainNumbers(disposition=Disposition.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainAffiliation(disposition=Disposition.WARN, data="metadata", field="authors"),
    )
