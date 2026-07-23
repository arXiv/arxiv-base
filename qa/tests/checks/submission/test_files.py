"""Tests for submission file checks."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry, SubmitEventInfo
from qa.checks.submission.files import DoesNotExceedTheFileSizeLimit


class TestOversizeCheck:
    def test_oversize_pass(self):
        sub_metadata = SubmitEventInfo(type="new", is_oversize=False, data_version=1, metadata_version=1)
        result = DoesNotExceedTheFileSizeLimit().run(QaDataRegistry(submit_event_info=sub_metadata))

        assert result.passed

    def test_oversize_fail(self):
        sub_metadata = SubmitEventInfo(type="new", is_oversize=True, data_version=1, metadata_version=1)
        result = DoesNotExceedTheFileSizeLimit().run(QaDataRegistry(submit_event_info=sub_metadata))

        assert not result.passed

    def test_missing_submit_event_info_raises(self):
        with pytest.raises(MissingDataError):
            DoesNotExceedTheFileSizeLimit().run(QaDataRegistry())
