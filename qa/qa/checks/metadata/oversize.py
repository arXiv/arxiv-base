
from qa.checks.base import BaseCheck
from qa.checks. models import OnFailurePolicy, QaDataRegistry, Result


class OversizeCheck(BaseCheck):
    name = "oversize"
    display_name = "Oversize"
    id = 48
    version = "0.1.0"
    description = "The oversize check fails on submissions which are too large."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Submission is oversize ."

    required_inputs = {"metadata"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        if data_registry.metadata.is_oversize:
            passed = False
            message = self.failure_message
            return self._result(passed=passed, message=message)
        else:
            return self._result(passed=True, message="")

        
