"""Author metadata checks."""

import re

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic


class AuthorsAreValid(BaseAggregateCheck):
    """Aggregate check for the metadata authors field."""

    name = "authors_are_valid"
    display_name = "Authors Are Valid"
    id = 200
    version = "1.0.0"
    description = "The metadata authors field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Authors are invalid or empty."

    required_data = {"metadata"}
    field = "authors"

    @classmethod
    def check(cls, authors: str | None, cleanup: bool = False) -> Result:
        if cleanup and authors is not None:
            authors = cls.cleanup(authors)
        return cls().run(QaDataRegistry(metadata=Metadata(authors=authors)))

    _checks = (
        generic.DoesNotEndWithPunctuation(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.DoesNotContainEtAl(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.DoesNotContainAnonymous(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.DoesNotContainCorresponding(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.AuthorNamesDoNotContainSemicolon(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"
        ),
        generic.DoesNotContainSpaceBeforeComma(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"
        ),
        generic.DoesNotContainTexDagger(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.DoesNotContainRawNewline(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.DoesNotContainTildeAsHardSpace(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"
        ),
        generic.DoesNotBeginWithAuthor(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"),
        generic.AuthorNamesDoNotContainPrefix(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"
        ),
        generic.AuthorNamesDoNotContainDegreeSuffix(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="authors"
        ),
        generic.NotAllCaps(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        generic.NotTooShort(
            min_chars=4,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="authors",
            failure_message="Too short: must be at least 4 characters.",
        ),
        generic.NotTooLong(
            max_chars=10000,
            on_failure_policy=OnFailurePolicy.WARN,
            data="metadata",
            field="authors",
            failure_message="Too long: must be 10000 characters or fewer.",
        ),
        generic.DoesNotContainAnnotationSymbols(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"
        ),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        generic.AuthorsDoNotContainLoneSurname(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"
        ),
        generic.AuthorsDoNotContainLlmAuthor(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        generic.AuthorNamesDoNotContainBrackets(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"
        ),
        generic.AuthorNamesDoNotContainNumbers(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"
        ),
        generic.AuthorNamesDoNotContainAffiliation(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"
        ),
        generic.DoesNotContainUnspacedComma(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
    )

    @staticmethod
    def cleanup(s: str) -> str:  # TODO check pre or post parsing
        """Perform some light tidying on the provided author string(s)."""
        s = re.sub(r"\s+", " ", s)  # Single spaces only.
        s = re.sub(r",(\s*,)+", ",", s)  # Remove double commas.
        # Add spaces between word and opening parenthesis.
        s = re.sub(r"(\w)\(", r"\g<1> (", s)
        # Add spaces between closing parenthesis and word.
        s = re.sub(r"\)(\w)", r") \g<1>", s)
        # Change capitalized or uppercase `And` to `and`.
        s = re.sub(r"\bA(?i:ND)\b", "and", s)
        return s.strip()  # Removing leading and trailing whitespace.
