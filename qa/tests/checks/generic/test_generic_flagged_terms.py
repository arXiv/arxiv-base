"""Tests for the generic flagged terms check."""

import pytest

from qa.checks.generic.flagged_terms import DoesNotContainFlaggedTerms
from qa.checks.models import FlaggedTermMatch, FlaggedTermsReport, Offset, OnFailurePolicy, QaDataRegistry


def match(field: str, keywords_id: int, keywords_name: str | None, text: str, starts_at=None, ends_at=None):
    return FlaggedTermMatch(
        field=field,
        keywords_id=keywords_id,
        keywords_name=keywords_name,
        match=text,
        starts_at=starts_at,
        ends_at=ends_at,
    )


def inputs(*matches: FlaggedTermMatch) -> QaDataRegistry:
    return QaDataRegistry(flagged_terms_report=FlaggedTermsReport(data=list(matches)))


def make(field: str) -> DoesNotContainFlaggedTerms:
    return DoesNotContainFlaggedTerms(on_failure_policy=OnFailurePolicy.WARN, data="flagged_terms_report", field=field)


class TestDoesNotContainFlaggedTerms:
    check = make("title")

    def test_pass_when_no_matches(self):
        result = self.check.run(inputs())
        assert result.passed
        assert result.offsets is None

    def test_pass_when_matches_are_in_other_fields(self):
        assert self.check.run(inputs(match("fulltext", 1, "alpha", " alpha ", 10, 17))).passed

    def test_fail_lists_each_term_once_in_order_found(self):
        result = self.check.run(
            inputs(
                match("title", 2, "beta", " beta ", 5, 11),
                match("title", 1, "alpha", " Alpha,", 20, 27),
                match("title", 2, "beta", " beta ", 40, 46),
            )
        )
        assert not result.passed
        assert result.message == "Flagged terms found: beta, alpha"

    def test_offsets_for_every_match_in_field(self):
        result = self.check.run(
            inputs(
                match("title", 1, "alpha", " alpha ", 5, 12),
                match("fulltext", 1, "alpha", " alpha ", 900, 907),
                match("title", 1, "alpha", " alpha,", 30, 37),
            )
        )
        assert result.offsets == [Offset(start=5, end=12), Offset(start=30, end=37)]

    def test_offsets_skip_matches_without_positions(self):
        result = self.check.run(
            inputs(
                match("title", 1, "alpha", " alpha ", 10, 17),
                match("title", 2, "beta", " beta "),
                match("title", 3, "gamma", " gamma ", 30, None),
            )
        )
        assert result.message == "Flagged terms found: alpha, beta, gamma"
        assert result.offsets == [Offset(start=10, end=17)]

    def test_no_offsets_when_report_has_none(self):
        result = self.check.run(inputs(match("title", 1, "alpha", " alpha ")))
        assert not result.passed
        assert result.offsets is None

    def test_term_falls_back_to_match_text(self):
        result = self.check.run(inputs(match("title", 1, None, " alpha,", 10, 17)))
        assert result.message == "Flagged terms found: alpha,"

    def test_config_includes_field(self):
        assert make("fulltext").config["field"] == "fulltext"

    def test_none_flagged_terms_report_raises(self):
        with pytest.raises(AssertionError):
            self.check._run(QaDataRegistry(flagged_terms_report=None))
