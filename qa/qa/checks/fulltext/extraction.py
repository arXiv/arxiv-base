from qa.checks.base import BaseCheck

from qa.checks.models import FulltextReport, OnFailurePolicy, QaDataRegistry, Result


class TextExtractionSuccessful(BaseCheck):
    name = "text_extraction_successful"
    display_name = "Text Extraction Successful"
    id = 14
    version = "1.0.0"
    description = "Text extraction was successful."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Text extraction failed."

    required_data = {"fulltext_report"}

    failure_flag_id = "text-extraction-failed"

    @classmethod
    def check(cls, fulltext_report: FulltextReport) -> Result:
        return cls().run(QaDataRegistry(fulltext_report=fulltext_report))

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


class TextNotCorruptedDuringExtraction(BaseCheck):
    """
    pdftotext writes a warning to the fulltext report when the extracted text has many garbled ligatures
    (ff, fi, ffi, ...), which suggests a non-Unicode font. IGNORE: record the result, but don't hold.
    """

    name = "text_not_corrupted_during_extraction"
    display_name = "Text Not Corrupted During Extraction"
    id = 29
    version = "1.0.0"
    description = "The extracted text was not corrupted by non-Unicode fonts."
    on_failure_policy = OnFailurePolicy.IGNORE
    failure_message = "Text corrupted during extraction - check for non-Unicode font?"

    required_data = {"fulltext_report"}

    @classmethod
    def check(cls, fulltext_report: FulltextReport) -> Result:
        return cls().run(QaDataRegistry(fulltext_report=fulltext_report))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext_report = data_registry.fulltext_report
        assert fulltext_report is not None

        warning = fulltext_report.data.get("warning")

        if warning:
            return self._result(passed=False, message=warning)
        return self._result(passed=True)
