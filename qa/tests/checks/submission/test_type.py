"""Tests for submission type checks."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import QaDataRegistry
from qa.checks.submission.type import IsNotAWithdrawal
from tests.utils import make_test_submit_event_info


class TestWithdrawalCheck:
    def test_wdr_pass(self):
        sub_metadata = make_test_submit_event_info()
        result = IsNotAWithdrawal().run(QaDataRegistry(submit_event_info=sub_metadata))

        assert result.passed

    def test_wdr_fail(self):
        sub_metadata = make_test_submit_event_info(type="wdr")
        result = IsNotAWithdrawal().run(QaDataRegistry(submit_event_info=sub_metadata))

        assert not result.passed

    def test_missing_submit_event_info_raises(self):
        with pytest.raises(MissingDataError):
            IsNotAWithdrawal().run(QaDataRegistry())
