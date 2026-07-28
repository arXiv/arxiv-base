"""Abstract metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    AllBracketsBalanced,
    AbstractAppearsToBeEnglish,
    DoesNotBeginWithAbstract,
    DoesNotContainControlCharsAllowNewlines,
    DoesNotContainRightarrowMacro,
    DoesNotContainTex,
    DoesNotContainTexBeginEnv,
    DoesNotContainTexHardSpaceAfterPeriod,
    DoesNotContainUnnecessaryEscape,
    DoesNotStartWithLowercase,
    NoBoundaryWhitespace,
    NoExcessiveCapitals,
    NoExtraWhitespace,
    NoHtmlElements,
    NoUnnecessarySpaceInParens,
    NoUtf8DecodingErrors,
    NotTooLong,
    NotTooManyLines,
    NotTooShort,
    UrlDoesNotEndWithPeriod,
)


class AbstractIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata abstract field."""

    name = "abstract_is_valid"
    display_name = "Abstract Is Valid"
    id = 300
    version = "1.0.0"
    description = "The metadata abstract field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Abstract is invalid or empty."

    required_data = {"metadata"}

    @classmethod
    def check(cls, abstract: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(abstract=abstract)))

    _checks = (
        NotTooShort(20, on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        NotTooLong(1920, on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        DoesNotBeginWithAbstract(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainTexBeginEnv(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainRightarrowMacro(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        DoesNotContainTexHardSpaceAfterPeriod(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"
        ),
        UrlDoesNotEndWithPeriod(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainControlCharsAllowNewlines(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        AbstractAppearsToBeEnglish(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        NotTooManyLines(24, on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
    )
