"""Author metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
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
    NoAnnotationSymbols,
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


class AuthorsAreValid(BaseAggregateCheck):
    """Aggregate check for the metadata authors field."""

    name = "authors_are_valid"
    id = 4
    version = "1.0.0"
    description = "The metadata authors field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Authors are invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, authors: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(authors=authors)))

    _checks = (
        NotEmpty(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        NotTooShort(4, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NotTooLong(10000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoAnnotationSymbols(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainAnonymous(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainCorresponding(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainTexDagger(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotBeginWithAuthor(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainTildeAsHardSpace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotEndWithPunctuation(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorsDoNotContainLoneSurname(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorsDoNotContainLlmAuthor(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainSemicolon(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainBrackets(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainNumbers(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainAffiliation(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
    )
