"""Abstract metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import Inputs, OnFailurePolicy, Metadata, Result
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
    id = 520
    version = "1.0.0"
    description = "The metadata abstract field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Abstract is invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, abstract: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(abstract=abstract)))

    _checks = (
        NotEmpty(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        NotTooShort(5, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NotTooLong(2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotBeginWithAbstract(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainUnnecessaryEscape(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainTexBeginEnv(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        DoesNotContainControlCharsAllowNewlines(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
    )
