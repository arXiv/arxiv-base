"""Tests for TextExtractionSuccessful."""

from qa.checks.fulltext.extraction import TextExtractionSuccessful
from qa.checks.models import Flag, FulltextReport


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
