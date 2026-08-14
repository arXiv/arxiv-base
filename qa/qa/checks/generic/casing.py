"""Generic capitalization checks."""

from qa.checks.models import Result, QaDataRegistry
from qa.checks.base import BaseGenericCheck, BaseGenericPatternCheck


class DoesNotStartWithLowercase(BaseGenericPatternCheck):
    name = "does_not_start_with_lowercase"
    display_name = "Does Not Start With Lowercase"
    id = 10008
    version = "1.0.0"
    description = "The value does not start with a lowercase letter."
    failure_message = "Begins with a lowercase letter."

    _pattern = r"^[a-z]"


class NoExcessiveCapitals(BaseGenericCheck):
    name = "no_excessive_capitals"
    display_name = "No Excessive Capitals"
    id = 10007
    version = "1.0.0"
    description = "The value does not contain excessive capitals."
    failure_message = "Likely excessive capitalization."

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        num_caps = sum([c.isupper() for c in v])
        num_lower = sum([c.islower() for c in v])

        if num_caps <= num_lower * 2 + 7:
            return self._result(passed=True)
        else:
            return self._result(passed=False, message=self.failure_message)


class NotAllCaps(BaseGenericCheck):
    name = "not_all_caps"
    display_name = "Not All Caps"
    id = 10066
    version = "1.0.0"
    description = "The value is not entirely uppercase."
    failure_message = "Value is all caps."

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        if v.isupper():
            return self._result(passed=False, message=self.failure_message)
        return self._result(passed=True)
