"""Tests for submission type checks."""

from qa.checks.models import QaDataRegistry, SubmissionMetadata
from qa.checks.submission.type import IsNotAWithdrawal


class TestWithdrawalCheck:
    def test_wdr_pass(self):
        metadata = SubmissionMetadata(type="new", title="Test Title")
        result = IsNotAWithdrawal().run(QaDataRegistry(metadata=metadata))

        assert result.passed

    def test_wdr_fail(self):
        metadata = SubmissionMetadata(type="wdr", title="Test Title")
        result = IsNotAWithdrawal().run(QaDataRegistry(metadata=metadata))

        assert not result.passed
