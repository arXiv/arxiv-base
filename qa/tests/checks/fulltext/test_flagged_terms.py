"""Tests for NoFlaggedTerms."""

import json

import pytest

from qa.checks.fulltext.flagged_terms import NoFlaggedTerms
from qa.checks.models import FlaggedTermMatch, FlaggedTermsReport, Offset, QaDataRegistry


def match(keywords_id: int, keywords_name: str | None, text: str, starts_at: int | None, ends_at: int | None):
    return FlaggedTermMatch(
        field="fulltext",
        keywords_id=keywords_id,
        keywords_name=keywords_name,
        action="admin",
        match=text,
        starts_at=starts_at,
        ends_at=ends_at,
    )


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
                "keywords_name": "tortured phrase",
                "action": "admin",
                "action_message": "Hold for review",
                "description": "Known tortured phrase",
                "match": " counterfeit consciousness ",
                "starts_at": 40,
                "ends_at": 67,
                "context": "In this paper we apply counterfeit consciousness to the problem",
            },
            {
                "field": "fulltext",
                "keywords_id": 12,
                "keywords_name": "tortured phrase",
                "action": "admin",
                "action_message": "Hold for review",
                "description": "Known tortured phrase",
                "match": " counterfeit consciousness,",
                "starts_at": 1520,
                "ends_at": 1547,
                "context": "... methods of counterfeit consciousness, as shown ...",
            },
            {
                "field": "fulltext",
                "keywords_id": 31,
                "keywords_name": "regenerate response",
                "action": "comment",
                "action_message": None,
                "description": "LLM output artifact",
                "match": " Regenerate response\n",
                "starts_at": 9001,
                "ends_at": 9022,
                "context": "... as an AI language model. Regenerate response",
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
    def test_pass_when_no_matches(self):
        result = NoFlaggedTerms.check(report())
        assert result.passed
        assert result.offsets is None

    def test_fail_lists_each_term_once_in_order_found(self):
        result = NoFlaggedTerms.check(FlaggedTermsReport.model_validate_json(CONCERNING_WORDS_JSON))
        assert not result.passed
        assert result.message == "Flagged terms found: tortured phrase, regenerate response"

    def test_offsets_for_every_match(self):
        result = NoFlaggedTerms.check(FlaggedTermsReport.model_validate_json(CONCERNING_WORDS_JSON))
        assert result.offsets == [
            Offset(start=40, end=67),
            Offset(start=1520, end=1547),
            Offset(start=9001, end=9022),
        ]

    def test_offsets_skip_matches_without_positions(self):
        result = NoFlaggedTerms.check(
            report(
                match(1, "alpha", " alpha ", 10, 17),
                match(2, "beta", " beta ", None, None),
                match(3, "gamma", " gamma ", 30, None),
            )
        )
        assert not result.passed
        assert result.message == "Flagged terms found: alpha, beta, gamma"
        assert result.offsets == [Offset(start=10, end=17)]

    def test_no_offsets_when_report_has_none(self):
        result = NoFlaggedTerms.check(report(match(1, "alpha", " alpha ", None, None)))
        assert not result.passed
        assert result.offsets is None

    def test_term_falls_back_to_match_text(self):
        result = NoFlaggedTerms.check(report(match(1, None, " alpha,", 10, 17)))
        assert result.message == "Flagged terms found: alpha,"

    def test_none_flagged_terms_report_raises(self):
        with pytest.raises(AssertionError):
            NoFlaggedTerms()._run(QaDataRegistry(flagged_terms_report=None))
