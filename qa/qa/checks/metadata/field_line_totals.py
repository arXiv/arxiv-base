"""Cross-field line-count checks for metadata."""

from qa.checks.base import BaseCheck
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Metadata, Result


class MetadataFieldsTotalLinesNotExceeded(BaseCheck):
    """Combined line-count check across several metadata fields."""

    name = "metadata_fields_total_lines_not_exceeded"
    display_name = "Metadata Fields Total Lines Not Exceeded"
    id = 1000
    version = "1.0.0"
    description = (
        "The combined line count of the title, authors, comments, msc_class, acm_class, "
        "journal_ref, and doi fields does not exceed the limit."
    )
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Combined metadata fields exceed the total line limit."

    required_data = {"metadata"}

    max_total_lines = 25
    _fields = ("title", "authors", "comments", "msc_class", "acm_class", "journal_ref", "doi")

    @classmethod
    def check(cls, metadata: Metadata) -> Result:
        return cls().run(QaDataRegistry(metadata=metadata))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        assert data_registry.metadata is not None

        total_lines = 0
        for field in self._fields:
            value = getattr(data_registry.metadata, field)
            if value:
                total_lines += value.count("\n") + 1

        if total_lines <= self.max_total_lines:
            return self._result(passed=True)

        return self._result(passed=False, message=self.failure_message)
