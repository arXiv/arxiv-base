"""ACM class metadata checks."""

from qa.checks.base import BaseAggregateCheck
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks import generic


class AcmClassIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata acm_class field."""

    name = "acm_class_is_valid"
    display_name = "ACM Class Is Valid"
    id = 900
    version = "1.0.0"
    description = "The metadata acm_class field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "ACM class is invalid."

    required_data = {"metadata"}
    field = "acm_class"

    @classmethod
    def check(cls, acm_class: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(acm_class=acm_class)))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Both None and empty string are valid and should pass without running sub-checks."""
        if data_registry.metadata.acm_class in (None, ""):  # type: ignore
            return self._result(passed=True, results=[])
        return super()._run(data_registry)

    _checks = (
        generic.DoesNotContainSemicolon(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="acm_class"),
        generic.DoesNotContainUrl(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="acm_class"),
        generic.DoesNotContainDoi(on_failure_policy=OnFailurePolicy.REJECT, data="metadata", field="acm_class"),
        generic.NotTooLong(max_chars=160, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        generic.NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        generic.NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        generic.DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
        generic.NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="acm_class"),
    )
