"""Abstract metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, Disposition, Metadata, Result
from qa.checks.generic.text import (
    AllBracketsBalanced,
    DoesNotBeginWithAbstract,
    DoesNotContainControlCharsAllowNewlines,
    DoesNotContainTex,
    DoesNotContainTexBeginEnv,
    DoesNotContainUnnecessaryEscape,
    DoesNotStartWithLowercase,
    NoBoundaryWhitespace,
    NoExcessiveCapitals,
    NoExtraWhitespace,
    NoHtmlElements,
    NoUnnecessarySpaceInParens,
    NoUtf8DecodingErrors,
    NotEmpty,
    NotTooLong,
    NotTooShort,
)
# TODO: add an English language check (requires gcld3, which has no macOS arm64 wheel)


class AbstractIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata abstract field."""

    name = "abstract_is_valid"
    id = 2
    version = "1.0.0"
    description = "The metadata abstract field is valid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, abstract: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(abstract=abstract)))

    _checks = (
        NotEmpty(disposition=Disposition.REJECT, data="metadata", field="abstract"),
        NotTooShort(5, disposition=Disposition.WARN, data="metadata", field="abstract"),
        NotTooLong(2000, disposition=Disposition.WARN, data="metadata", field="abstract"),
        DoesNotBeginWithAbstract(disposition=Disposition.WARN, data="metadata", field="abstract"),
        NoExcessiveCapitals(disposition=Disposition.WARN, data="metadata", field="abstract"),
        DoesNotStartWithLowercase(disposition=Disposition.WARN, data="metadata", field="abstract"),
        DoesNotContainUnnecessaryEscape(disposition=Disposition.WARN, data="metadata", field="abstract"),
        DoesNotContainTex(disposition=Disposition.WARN, data="metadata", field="abstract"),
        DoesNotContainTexBeginEnv(disposition=Disposition.WARN, data="metadata", field="abstract"),
        NoBoundaryWhitespace(disposition=Disposition.WARN, data="metadata", field="abstract"),
        NoExtraWhitespace(disposition=Disposition.WARN, data="metadata", field="abstract"),
        NoUnnecessarySpaceInParens(disposition=Disposition.WARN, data="metadata", field="abstract"),
        NoHtmlElements(disposition=Disposition.WARN, data="metadata", field="abstract"),
        AllBracketsBalanced(disposition=Disposition.WARN, data="metadata", field="abstract"),
        DoesNotContainControlCharsAllowNewlines(disposition=Disposition.WARN, data="metadata", field="abstract"),
        NoUtf8DecodingErrors(disposition=Disposition.WARN, data="metadata", field="abstract"),
    )
