"""Generic presence checks."""

from qa.checks.base import BaseGenericCheck
from qa.checks.models import QaDataRegistry, Result


class EmptyFieldCheck(BaseGenericCheck):
    name = "field_is_not_empty"
    display_name = "Field Is Not Empty"
    id = 10072
    version = "1.0.0"
    description = "The field is not empty."
    failure_message = "Field is empty."

    _short_circuits_on_failure = True

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        if v in (None, ""):
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)
