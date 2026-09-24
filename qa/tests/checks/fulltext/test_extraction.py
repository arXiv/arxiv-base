"""Tests for text extraction checks."""

import pytest

from qa.checks.fulltext.extraction import TextExtractionSuccessful, TextNotCorruptedDuringExtraction
from qa.checks.models import Disposition, Flag, FulltextReport, QaDataRegistry


def fulltext_report(flags: list[Flag] | None = None) -> FulltextReport:
    return FulltextReport(submission_id=1, data={}, flags=flags or [])


class TestTextExtractionSuccessful:
    def test_pass_when_no_flags(self):
        result = TextExtractionSuccessful.check(fulltext_report())
        assert result.passed

    def test_fail_on_extraction_failed_flag(self):
        report = fulltext_report(
            flags=[
                Flag(
                    id="text-extraction-failed",
                    description="Text extraction failed: All extraction methods failed",
                )
            ],
        )
        result = TextExtractionSuccessful.check(report)
        assert not result.passed
        assert result.message == "Text extraction failed."

    def test_pass_with_unrelated_flags(self):
        report = fulltext_report(flags=[Flag(id="some-other-flag", description="unrelated")])
        result = TextExtractionSuccessful.check(report)
        assert result.passed

    def test_none_fulltext_report_raises(self):
        with pytest.raises(AssertionError):
            TextExtractionSuccessful()._run(QaDataRegistry(fulltext_report=None))


# The warning pdftotext's languageid_json writes when it finds more than 10 garbled ligatures.
LIGATURE_WARNING = "Text corrupted during extraction - check for non-Unicode font?"


class TestTextNotCorruptedDuringExtraction:
    def test_pass_without_warning(self):
        report = FulltextReport(submission_id=1, data={"warning": ""})
        assert TextNotCorruptedDuringExtraction.check(report).passed

    def test_pass_when_warning_missing(self):
        """e.g. the report written when text extraction failed."""
        assert TextNotCorruptedDuringExtraction.check(fulltext_report()).passed

    def test_fail_on_warning(self):
        report = FulltextReport(submission_id=1, data={"warning": LIGATURE_WARNING})
        result = TextNotCorruptedDuringExtraction.check(report)
        assert not result.passed
        assert result.message == LIGATURE_WARNING

    def test_failure_does_not_hold(self):
        """Like docsim, record the result as ok without holding."""
        report = FulltextReport(submission_id=1, data={"warning": LIGATURE_WARNING})
        assert TextNotCorruptedDuringExtraction.check(report).disposition == Disposition.OK

    def test_none_fulltext_report_raises(self):
        with pytest.raises(AssertionError):
            TextNotCorruptedDuringExtraction()._run(QaDataRegistry(fulltext_report=None))
