"""Tests for NoFlaggedTerms."""

import json

from qa.checks.fulltext.flagged_terms import FLAGGED_TERMS_FIELDS, NoFlaggedTerms
from qa.checks.models import Disposition, FlaggedTermMatch, FlaggedTermsReport, Offset


def report(*matches: FlaggedTermMatch) -> FlaggedTermsReport:
    return FlaggedTermsReport(data=list(matches))


# Shaped like the {submission_id}.concerning_words.json written by the arxiv-qa concerning_words cloud function.
CONCERNING_WORDS_JSON = json.dumps(
    {
        "version": "1.0",
        "name": "concerning-words",
        "data": [
            {
                "field": "abstract",
                "keywords_id": 12,
                "keywords_name": "fake term one",
                "action": "admin",
                "action_message": "Hold for review",
                "description": "Test flagged term",
                "match": " fake term one ",
                "starts_at": 40,
                "ends_at": 55,
                "context": "In this paper we apply fake term one to the problem",
            },
            {
                "field": "fulltext",
                "keywords_id": 12,
                "keywords_name": "fake term one",
                "action": "admin",
                "action_message": "Hold for review",
                "description": "Test flagged term",
                "match": " Fake term one,",
                "starts_at": 1520,
                "ends_at": 1535,
                "context": "... methods of Fake term one, as shown ...",
            },
            {
                "field": "fulltext",
                "keywords_id": 31,
                "keywords_name": "fake term two",
                "action": "comment",
                "action_message": None,
                "description": "Another test flagged term",
                "match": " fake term two\n",
                "starts_at": 9001,
                "ends_at": 9015,
                "context": "... end of the paper. fake term two",
            },
        ],
        "metadata": {
            "ran_at": "2026-09-24 14:03:11.000000",
            "fulltext-length": 48211,
            "categories": ["cs.AI"],
            "source_format": "tex",
            "pdf_generation": 1721303583515340,
            "metadata_generation": 1721303590112233,
            "submit_time": "2026-09-24 13:58:02",
            "action": "admin",
            "duration": "0.412",
        },
    }
)


def sub_result(result, field):
    return next(r for r in result.results if r.check_config["field"] == field)


class TestFlaggedTermsReport:
    def test_parses_cloud_function_output(self):
        parsed = FlaggedTermsReport.model_validate_json(CONCERNING_WORDS_JSON)
        assert parsed.name == "concerning-words"
        assert len(parsed.data) == 3
        assert parsed.data[0].field == "abstract"
        assert parsed.data[0].starts_at == 40
        assert parsed.metadata["action"] == "admin"

    def test_empty_report(self):
        parsed = FlaggedTermsReport.model_validate_json('{"version": "1.0", "name": "concerning-words", "data": []}')
        assert parsed.data == []


class TestNoFlaggedTerms:
    def test_one_sub_check_per_field(self):
        assert [c.field for c in NoFlaggedTerms._checks] == list(FLAGGED_TERMS_FIELDS)
        assert len(NoFlaggedTerms()._describe()["checks"]) == len(FLAGGED_TERMS_FIELDS)

    def test_pass_when_no_matches(self):
        result = NoFlaggedTerms.check(report())
        assert result.passed
        assert result.disposition == Disposition.OK
        assert result.message == ""
        assert result.results is not None
        assert all(r.passed for r in result.results)

    def test_fail_lists_each_term_once_across_fields(self):
        result = NoFlaggedTerms.check(FlaggedTermsReport.model_validate_json(CONCERNING_WORDS_JSON))
        assert not result.passed
        assert result.disposition == Disposition.WARN
        assert result.message == "Flagged terms found: fake term one, fake term two"

    def test_sub_results_by_field(self):
        result = NoFlaggedTerms.check(FlaggedTermsReport.model_validate_json(CONCERNING_WORDS_JSON))

        abstract = sub_result(result, "abstract")
        assert not abstract.passed
        assert abstract.message == "Flagged terms found: fake term one"
        assert abstract.offsets == [Offset(start=40, end=55)]

        fulltext = sub_result(result, "fulltext")
        assert not fulltext.passed
        assert fulltext.message == "Flagged terms found: fake term one, fake term two"
        assert fulltext.offsets == [Offset(start=1520, end=1535), Offset(start=9001, end=9015)]

        for field in ("title", "authors", "comments", "journal_ref"):
            assert sub_result(result, field).passed

    def test_ignores_matches_in_unsearched_fields(self):
        result = NoFlaggedTerms.check(
            report(FlaggedTermMatch(field="report_num", keywords_id=1, keywords_name="alpha", match=" alpha "))
        )
        assert result.passed
