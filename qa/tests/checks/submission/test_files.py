"""Tests for submission file checks."""

from qa.checks.models import QaDataRegistry, SubmissionMetadata
from qa.checks.submission.files import DoesNotExceedTheFileSizeLimit


class TestOversizeCheck:
    def test_oversize_pass(self):
        metadata = SubmissionMetadata(type="new", title="Test Title", is_oversize=False)
        result = DoesNotExceedTheFileSizeLimit().run(QaDataRegistry(metadata=metadata))

        assert result.passed

    def test_oversize_fail(self):
        metadata = SubmissionMetadata(type="new", title="Test Title", is_oversize=True)
        result = DoesNotExceedTheFileSizeLimit().run(QaDataRegistry(metadata=metadata))

        assert not result.passed
