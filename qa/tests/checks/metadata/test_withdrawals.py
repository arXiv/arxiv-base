"""Tests for AbstractIsValid."""

from qa.checks.models import QaDataRegistry, SubmissionMetadata
from qa.checks.metadata.withdrawal import WithdrawalCheck


class TestWithdrawalCheck:
    def test_new_pass(self):
        check = WithdrawalCheck()
        metadata = SubmissionMetadata(type="new", title="Test Title")
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert result.passed

    def test_rep_pass(self):
        check = WithdrawalCheck()
        metadata = SubmissionMetadata(type="rep", title="Test Title")
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert result.passed
        
    def test_wdr_fail(self):
        check = WithdrawalCheck()
        metadata = SubmissionMetadata(type="wdr", title="Test Title")
        registry = QaDataRegistry(metadata=metadata)
        result = check._run(registry)
        assert not result.passed
        
