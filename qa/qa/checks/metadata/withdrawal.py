
from qa.checks.base import BaseCheck

from qa.checks. models import OnFailurePolicy, QaDataRegistry, Result


class WithdrawalCheck(BaseCheck):
    """Check for withdrawals, which require staff approval."""

    name = "withdrawal"
    display_name = "Withdrawal"
    id = 14
    version = "1.0.0"
    description = "Review all withdrawals."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "<Withdrawal requires staff approval."

    required_inputs = {"metadata"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        assert data_registry.metadata is not None
        _type = data_registry.metadata.type

        if _type == "wdr":
            passed = False
            return self._result(passed, message = self.failure_message)
        else:
            passed = True
            return self._result(passed)
        
        
