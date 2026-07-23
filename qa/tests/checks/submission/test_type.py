"""Tests for submission type checks."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry, SubmissionPubsubInfo
from qa.checks.submission.type import IsNotAWithdrawal


class TestWithdrawalCheck:
    def test_wdr_pass(self):
        sub_metadata = SubmissionPubsubInfo(type="new", is_oversize=False, data_version=1, metadata_version=1)
        result = IsNotAWithdrawal().run(QaDataRegistry(submission_pubsub_info=sub_metadata))

        assert result.passed

    def test_wdr_fail(self):
        sub_metadata = SubmissionPubsubInfo(type="wdr", is_oversize=False, data_version=1, metadata_version=1)
        result = IsNotAWithdrawal().run(QaDataRegistry(submission_pubsub_info=sub_metadata))

        assert not result.passed

    def test_missing_submission_pubsub_info_raises(self):
        with pytest.raises(MissingDataError):
            IsNotAWithdrawal().run(QaDataRegistry())
