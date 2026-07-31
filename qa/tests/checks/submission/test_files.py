"""Tests for submission file checks."""

import pytest
from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry
from qa.checks.submission.files import DoesNotExceedTheFileSizeLimit
from tests.utils import make_test_submit_event_info


class TestOversizeCheck:
    def test_oversize_pass(self):
        sub_metadata = make_test_submit_event_info()
        result = DoesNotExceedTheFileSizeLimit().run(QaDataRegistry(submit_event_info=sub_metadata))

        assert result.passed

    def test_oversize_fail(self):
        sub_metadata = make_test_submit_event_info(is_oversize=True)
        result = DoesNotExceedTheFileSizeLimit().run(QaDataRegistry(submit_event_info=sub_metadata))

        assert not result.passed

    def test_missing_submit_event_info_raises(self):
        with pytest.raises(MissingDataError):
            DoesNotExceedTheFileSizeLimit().run(QaDataRegistry())
