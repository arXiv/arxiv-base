"""Tests for fulltext structure checks."""

import pytest

from qa.checks.fulltext.structure import FulltextNotTooShort
from qa.checks.models import QaDataRegistry


class TestFulltextNotTooShort:
    def test_pass_normal(self):
        text = "In this work, we study aaa, bbb, and ccc and conclude ddd. " * 140

        result = FulltextNotTooShort.check(text)
        assert result.passed

    def test_fail_nospaces(self):
        text = "Inthiswork, westudyaaa, bbb, andcccandconcludeddd. " * 100

        result = FulltextNotTooShort.check(text)
        assert not result.passed

    def test_fail_on_empty(self):
        result = FulltextNotTooShort.check("")
        assert not result.passed

    def test_none_fulltext_raises(self):
        with pytest.raises(AssertionError):
            FulltextNotTooShort()._run(QaDataRegistry(fulltext=None))
