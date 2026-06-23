"""Tests for AbstractIsValid."""

from qa.checks.models import QaDataRegistry
from qa.checks.fulltext.text_checks import (
    MissingTextCheck,
    VeryShortTextCheck,
)

class TestMissingText:
    def test_pass_normal(self):
        text = "In this work, we study aaa, bbb, and ccc and conclude ddd. "
        result = MissingTextCheck().run(QaDataRegistry(fulltext=text))
        assert result.passed
        
    def test_fail_on_none(self):
        text = None
        result = MissingTextCheck().run(QaDataRegistry(fulltext=text))
        assert not result.passed

    def test_fail_on_empty(self):
        text = ""
        result = MissingTextCheck().run(QaDataRegistry(fulltext=text))
        assert not result.passed

class TestVeryShortText:
    def test_pass_normal(self):
        text = "In this work, we study aaa, bbb, and ccc and conclude ddd. " * 140

        result = VeryShortTextCheck().run(QaDataRegistry(fulltext=text))
        assert result.passed
        
    def test_fail_nospaces(self):
        text = "Inthiswork, westudyaaa, bbb, andcccandconcludeddd. " * 100
        
        result = VeryShortTextCheck().run(QaDataRegistry(fulltext=text))
        assert not result.passed

