"""Tests for AbstractIsValid."""

from qa.checks.models import QaDataRegistry
from qa.checks.fulltext.text_checks import (
    FulltextExtractedCheck,
    FulltextNotTooShortCheck,
)

class TestFulltextExtractedCheck:
    def test_pass_normal(self):
        text = "In this work, we study aaa, bbb, and ccc and conclude ddd. "
        result = FulltextExtractedCheck().run(QaDataRegistry(fulltext=text))
        assert result.passed
        
    def test_fail_on_none(self):
        text = None
        result = FulltextExtractedCheck().run(QaDataRegistry(fulltext=text))
        assert not result.passed

    def test_fail_on_empty(self):
        text = ""
        result = FulltextExtractedCheck().run(QaDataRegistry(fulltext=text))
        assert not result.passed

class TestFulltextNotTooShortCheck:
    def test_pass_normal(self):
        text = "In this work, we study aaa, bbb, and ccc and conclude ddd. " * 140

        result = FulltextNotTooShortCheck().run(QaDataRegistry(fulltext=text))
        assert result.passed
        
    def test_fail_nospaces(self):
        text = "Inthiswork, westudyaaa, bbb, andcccandconcludeddd. " * 100
        
        result = FulltextNotTooShortCheck().run(QaDataRegistry(fulltext=text))
        assert not result.passed

