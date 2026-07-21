"""Tests for fulltext structure checks."""

from qa.checks.models import QaDataRegistry
from qa.checks.fulltext.structure import FulltextNotTooShort


class TestFulltextNotTooShort:
    def test_pass_normal(self):
        text = "In this work, we study aaa, bbb, and ccc and conclude ddd. " * 140

        result = FulltextNotTooShort().run(QaDataRegistry(fulltext=text))
        assert result.passed

    def test_fail_nospaces(self):
        text = "Inthiswork, westudyaaa, bbb, andcccandconcludeddd. " * 100

        result = FulltextNotTooShort().run(QaDataRegistry(fulltext=text))
        assert not result.passed

    def test_pass_on_none(self):
        result = FulltextNotTooShort().run(QaDataRegistry(fulltext=None))
        assert result.passed

    def test_pass_on_empty(self):
        result = FulltextNotTooShort().run(QaDataRegistry(fulltext=""))
        assert result.passed
