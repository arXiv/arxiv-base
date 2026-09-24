"""Tests for AuthorsFoundInFulltext."""

import json

import pytest

from qa.checks.fulltext.authors import AuthorsFoundInFulltext
from qa.checks.models import AuthorCheckReport, Flag, QaDataRegistry


def author_report(flags: list[Flag] | None = None) -> AuthorCheckReport:
    return AuthorCheckReport(submission_id=1, data={}, flags=flags or [])


# Shaped like the {submission_id}.author-check.json written by the arxiv-qa check_authors cloud function.
AUTHOR_CHECK_JSON = json.dumps(
    {
        "name": "arXiv Author Metadata Report",
        "key_name": "author-check",
        "version": "1.1",
        "submission_id": 3908742,
        "created": "2026-09-24T14:03:11.000000+00:00",
        "flags": [
            {
                "id": "missing-authors-fulltext",
                "description": "Author (A. Anitra) not found in text.",
            }
        ],
        "qa_exec_time_sec": 0,
        "data": {
            "num_metadata_authors": 9,
            "bad_authors": [],
            "missing_authors": ["A. Anitra"],
            "anonymous_authors": [],
            "short_text": False,
            "pdf_generation": 1721303583515340,
            "metadata_generation": 1721303590112233,
        },
    }
)


class TestAuthorCheckReport:
    def test_defaults(self):
        report = author_report()
        assert report.name == "arXiv Author Metadata Report"
        assert report.key_name == "author-check"
        assert report.version == "1.1"

    def test_parses_cloud_function_output(self):
        report = AuthorCheckReport.model_validate_json(AUTHOR_CHECK_JSON)
        assert report.submission_id == 3908742
        assert report.flags[0].id == "missing-authors-fulltext"
        assert report.data["missing_authors"] == ["A. Anitra"]


class TestAuthorsFoundInFulltext:
    def test_pass_when_no_flags(self):
        result = AuthorsFoundInFulltext.check(author_report())
        assert result.passed

    def test_fail_on_missing_authors_flag(self):
        result = AuthorsFoundInFulltext.check(AuthorCheckReport.model_validate_json(AUTHOR_CHECK_JSON))
        assert not result.passed
        assert result.message == "Author (A. Anitra) not found in text."

    def test_fail_on_anonymous_authors_flag(self):
        report = author_report(
            flags=[
                Flag(
                    id="anonymous-authors",
                    description="Found: Anonymous - Check for potential anonymous authors.",
                )
            ],
        )
        result = AuthorsFoundInFulltext.check(report)
        assert not result.passed
        assert result.message == "Found: Anonymous - Check for potential anonymous authors."

    def test_fail_on_bad_authors_flag(self):
        report = author_report(
            flags=[Flag(id="bad-authors", description="Found: 123 - Check for potential bad author names.")],
        )
        assert not AuthorsFoundInFulltext.check(report).passed

    def test_message_joins_all_failing_flags(self):
        report = author_report(
            flags=[
                Flag(id="anonymous-authors", description="Found: Anonymous - Check for potential anonymous authors."),
                Flag(id="missing-authors-fulltext", description="Author (A. Anitra) not found in text."),
            ],
        )
        result = AuthorsFoundInFulltext.check(report)
        assert result.message == (
            "Found: Anonymous - Check for potential anonymous authors. Author (A. Anitra) not found in text."
        )

    def test_default_message_when_flag_has_no_description(self):
        report = author_report(flags=[Flag(id="missing-authors-fulltext", description=None)])
        assert AuthorsFoundInFulltext.check(report).message == "Author check failed."

    def test_pass_with_unrelated_flags(self):
        report = author_report(flags=[Flag(id="some-other-flag", description="unrelated")])
        assert AuthorsFoundInFulltext.check(report).passed

    def test_none_author_report_raises(self):
        with pytest.raises(AssertionError):
            AuthorsFoundInFulltext()._run(QaDataRegistry(author_report=None))
