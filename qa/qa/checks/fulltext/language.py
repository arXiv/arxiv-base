"""Checks on the per-page language identification that pdftotext writes to the fulltext report."""

from qa.checks.base import BaseCheck

from qa.checks.models import FulltextReport, OnFailurePolicy, QaDataRegistry, Result

UNKNOWN_LANGUAGE = "un"  # what pdftotext records for a page cld2 cannot reliably identify


def _language_id(fulltext_report: FulltextReport) -> tuple[str | None, str | None, dict[str, int]]:
    """Return the most common language, the second most common language, and the page count per language."""
    lid = fulltext_report.data.get("language_id") or {}
    return lid.get("language"), lid.get("language2"), lid.get("languages") or {}


def _is_unrecognized(language: str | None, language2: str | None) -> bool:
    """Mostly unknown pages, unless the second language is English (QA-140)."""
    return language == UNKNOWN_LANGUAGE and language2 != "en"


class FulltextLanguageRecognized(BaseCheck):
    name = "fulltext_language_recognized"
    display_name = "Fulltext Language Recognized"
    id = 16
    version = "1.0.0"
    description = "The language of most full text pages was recognized."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Language not recognized. Check full text."

    required_data = {"fulltext_report"}

    @classmethod
    def check(cls, fulltext_report: FulltextReport) -> Result:
        return cls().run(QaDataRegistry(fulltext_report=fulltext_report))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext_report = data_registry.fulltext_report
        assert fulltext_report is not None

        language, language2, _ = _language_id(fulltext_report)

        if _is_unrecognized(language, language2):
            return self._result(passed=False, message=self.failure_message)
        return self._result(passed=True)


class FulltextHasEnoughEnglish(BaseCheck):
    name = "fulltext_has_enough_english"
    display_name = "Fulltext Has Enough English"
    id = 17
    version = "1.0.0"
    description = "A non-English full text includes an English version."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Multilanguage submission. Check for English version."

    required_data = {"fulltext_report"}

    min_english_ratio = 0.30  # of identified pages

    @classmethod
    def check(cls, fulltext_report: FulltextReport) -> Result:
        return cls().run(QaDataRegistry(fulltext_report=fulltext_report))

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "min_english_ratio": self.min_english_ratio,
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext_report = data_registry.fulltext_report
        assert fulltext_report is not None

        language, language2, languages = _language_id(fulltext_report)

        # Unrecognized text is reported by FulltextLanguageRecognized instead.
        if language is None or language == "en" or _is_unrecognized(language, language2):
            return self._result(passed=True)

        num_pages = sum(languages.values())
        if languages.get("en", 0) < self.min_english_ratio * num_pages:
            return self._result(passed=False, message=self.failure_message)
        return self._result(passed=True)
