"""Tests for TextExtractionSuccessful."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.fulltext.extraction import TextExtractionSuccessful
from qa.checks.models import Flag, FulltextReport, QaDataRegistry


def fulltext_report(flags: list[Flag] | None = None) -> FulltextReport:
    return FulltextReport(submission_id=1, data={}, flags=flags or [])


class TestTextExtractionSuccessful:
    def test_pass_when_no_flags(self):
        report = fulltext_report()
        result = TextExtractionSuccessful().run(QaDataRegistry(fulltext_report=report))
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
        result = TextExtractionSuccessful().run(QaDataRegistry(fulltext_report=report))
        assert not result.passed
        assert result.message == "Text extraction failed."

    def test_pass_with_unrelated_flags(self):
        report = fulltext_report(flags=[Flag(id="some-other-flag", description="unrelated")])
        result = TextExtractionSuccessful().run(QaDataRegistry(fulltext_report=report))
        assert result.passed

    def test_missing_fulltext_report_raises(self):
        with pytest.raises(MissingDataError):
            TextExtractionSuccessful().run(QaDataRegistry())
