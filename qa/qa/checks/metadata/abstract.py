"""Abstract metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic
# TODO: add an English language check (requires gcld3, which has no macOS arm64 wheel)


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
    field = "abstract"

    @classmethod
    def check(cls, abstract: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(abstract=abstract)))

    _checks = (
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="abstract"),
        generic.NotTooShort(min_chars=150, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NotTooLong(max_chars=2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotBeginWithAbstract(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoExcessiveCapitals(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotStartWithLowercase(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainUnnecessaryEscape(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
        generic.DoesNotContainHrefOrUrlTex(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainTexBegin(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"),
        generic.DoesNotContainControlCharsAllowNewlines(
            on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract"
        ),
    )
