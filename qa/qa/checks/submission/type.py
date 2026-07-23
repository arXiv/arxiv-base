"""Submission type checks."""

from qa.checks.base import BaseCheck
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result


class IsNotAWithdrawal(BaseCheck):
    name = "is_not_a_withdrawal"
    display_name = "Is Not A Withdrawal"
    id = 49
    version = "1.0.0"
    description = "The submission is not a withdrawal."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "The submission is a withdrawal which requires staff approval."

    required_data = {"submit_event_info"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        assert data_registry.submit_event_info is not None

        _type = data_registry.submit_event_info.type

        if _type == "wdr":
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)
