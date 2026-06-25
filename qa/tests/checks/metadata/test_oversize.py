"""Tests for AbstractIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import OnFailurePolicy, QaDataRegistry, SubmissionMetadata, Result
from qa.checks.metadata.oversize import OversizeCheck


class TestOversizeCheck:
    def test_new_pass(self):
        check = OversizeCheck()
        metadata = SubmissionMetadata(
            type="new",
            title="Test Title",
            is_oversize=False)
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert result.passed

    def test_rep_pass(self):
        check = OversizeCheck()
        metadata = SubmissionMetadata(
            type="rep",
            title="Test Title",
            is_oversize=False)
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert result.passed
        
    def test_cross_pass(self):
        check = OversizeCheck()
        metadata = SubmissionMetadata(
            type="cross",
            title="Test Title",
            is_oversize=False)
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert result.passed
        
    def test_oversize_fail(self):
        check = OversizeCheck()
        metadata = SubmissionMetadata(
            type="new",
            title="Test Title",
            is_oversize=True)
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert not result.passed

    def test_oversize_rep_fail(self):
        check = OversizeCheck()
        metadata = SubmissionMetadata(
            type="rep",
            title="Test Title",
            is_oversize=True)
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert not result.passed
        
