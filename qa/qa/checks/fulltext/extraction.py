from qa.checks.base import BaseCheck

from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result


class TextExtractionSuccessful(BaseCheck):
    name = "text_extraction_successful"
    display_name = "Text Extraction Successful"
    id = 14
    version = "1.0.0"
    description = "Text extraction was successful."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Text extraction failed."

    required_data = {"fulltext_report"}

    failure_flag_id = "text-extraction-failed"

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "failure_flag_id": self.failure_flag_id,
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext_report = data_registry.fulltext_report
        assert fulltext_report is not None

        extraction_failed = any(flag.id == self.failure_flag_id for flag in fulltext_report.flags)

        if extraction_failed:
            return self._result(passed=False, message=self.failure_message)
        return self._result(passed=True)
