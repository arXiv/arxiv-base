"""Tests for fulltext language checks."""

import pytest

from qa.checks.fulltext.language import FulltextHasEnoughEnglish, FulltextLanguageRecognized
from qa.checks.models import FulltextReport, QaDataRegistry


def fulltext_report(languages: dict[str, int] | None = None, language_id: dict | None = None) -> FulltextReport:
    """Build a report with language_id shaped like pdftotext's languageid_json output."""
    if language_id is None and languages is not None:
        ranked = sorted(languages, key=lambda lang: -languages[lang])
        language_id = {
            "language": ranked[0] if ranked else None,
            "language2": ranked[1] if len(ranked) > 1 else None,
            "languages": languages,
            "num_short_pages": 0,
            "num_unreliable": languages.get("un", 0),
        }
    data: dict = {"files": [], "pdf_generation": 1721303583515340, "warning": ""}
    if language_id is not None:
        data["language_id"] = language_id
    return FulltextReport(submission_id=1, data=data)


class TestFulltextLanguageRecognized:
    def test_pass_english(self):
        assert FulltextLanguageRecognized.check(fulltext_report({"en": 12, "un": 3})).passed

    def test_pass_other_language(self):
        assert FulltextLanguageRecognized.check(fulltext_report({"fr": 10})).passed

    def test_fail_mostly_unknown(self):
        result = FulltextLanguageRecognized.check(fulltext_report({"un": 10, "fr": 2}))
        assert not result.passed
        assert result.message == "Language not recognized. Check full text."

    def test_fail_all_unknown(self):
        assert not FulltextLanguageRecognized.check(fulltext_report({"un": 10})).passed

    def test_pass_unknown_with_english_second(self):
        """QA-140: mostly unknown is fine when the second language is English."""
        assert FulltextLanguageRecognized.check(fulltext_report({"un": 10, "en": 5})).passed

    def test_pass_no_pages_identified(self):
        assert FulltextLanguageRecognized.check(fulltext_report({})).passed

    def test_pass_without_language_id(self):
        """e.g. the report written when text extraction failed."""
        assert FulltextLanguageRecognized.check(fulltext_report()).passed

    def test_none_fulltext_report_raises(self):
        with pytest.raises(AssertionError):
            FulltextLanguageRecognized()._run(QaDataRegistry(fulltext_report=None))


class TestFulltextHasEnoughEnglish:
    def test_pass_english(self):
        assert FulltextHasEnoughEnglish.check(fulltext_report({"en": 12, "de": 3})).passed

    def test_fail_not_enough_english(self):
        result = FulltextHasEnoughEnglish.check(fulltext_report({"fr": 10, "en": 2}))
        assert not result.passed
        assert result.message == "Multilanguage submission. Check for English version."

    def test_fail_no_english(self):
        assert not FulltextHasEnoughEnglish.check(fulltext_report({"ru": 8})).passed

    def test_pass_at_threshold(self):
        """3 of 10 pages is exactly 30% English."""
        assert FulltextHasEnoughEnglish.check(fulltext_report({"es": 7, "en": 3})).passed

    def test_fail_just_under_threshold(self):
        assert not FulltextHasEnoughEnglish.check(fulltext_report({"es": 8, "en": 3})).passed

    def test_pass_when_unrecognized(self):
        """Left to FulltextLanguageRecognized, as in docsim's if/elif."""
        assert FulltextHasEnoughEnglish.check(fulltext_report({"un": 10, "fr": 2})).passed

    def test_fail_unknown_with_little_english(self):
        """Mostly unknown with English second is not 'unrecognized' (QA-140), so the English ratio applies."""
        assert not FulltextHasEnoughEnglish.check(fulltext_report({"un": 10, "en": 2})).passed

    def test_pass_no_pages_identified(self):
        assert FulltextHasEnoughEnglish.check(fulltext_report({})).passed

    def test_pass_without_language_id(self):
        assert FulltextHasEnoughEnglish.check(fulltext_report()).passed

    def test_config_includes_threshold(self):
        assert FulltextHasEnoughEnglish().config["min_english_ratio"] == 0.30

    def test_none_fulltext_report_raises(self):
        with pytest.raises(AssertionError):
            FulltextHasEnoughEnglish()._run(QaDataRegistry(fulltext_report=None))
