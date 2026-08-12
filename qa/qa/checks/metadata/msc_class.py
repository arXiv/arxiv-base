"""MSC class metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic


class MscClassIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata msc_class field."""

    name = "msc_class_is_valid"
    display_name = "MSC Class Is Valid"
    id = 800
    version = "1.0.0"
    description = "The metadata msc_class field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "MSC class is invalid."

    required_data = {"metadata"}
    field = "msc_class"

    @classmethod
    def check(cls, msc_class: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(msc_class=msc_class)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.msc_class in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="msc_class"),
        generic.NoUnnecessarySpaceInParens(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="msc_class"
        ),
        generic.DoesNotContainControlChars(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="msc_class"
        ),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="msc_class"),
        generic.DoesNotContainSemicolon(
            on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="msc_class"
        ),  # TODO remove?
        generic.NotTooLong(max_chars=160, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="msc_class"),
    )
