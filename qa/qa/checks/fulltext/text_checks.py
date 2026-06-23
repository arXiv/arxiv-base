
from qa.checks.base import BaseCheck

from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result


class MissingTextCheck(BaseCheck):
    """Check for missing text (probably PDF invalid or password protected)."""

    name = "missing_text"
    display_name = "Missing Text"
    id = 14
    version = "1.0.0"
    description = "Failed to extract text."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Missing text (check PDF?)"

    required_inputs = {"fulltext"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext = data_registry.fulltext
        if fulltext is not None and fulltext != "":
            passed = True
            return self._result(passed)
        else:
            passed = False
            return self._result(passed, message = self.failure_message)
        

class VeryShortTextCheck(BaseCheck):
    """Check for very short text."""

    name = "short_text"
    display_name = "Short Text"
    id = 15
    version = "1.0.0"
    description = "The full text extracted is too short."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Very short text (< 1400 words). Check full text."
    
    required_inputs = {"fulltext"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext = data_registry.fulltext
        if fulltext is None or fulltext is "":
            # Problem: we should only report the problem with missing texts
            passed = True
            return self._result(passed)
        elif len(fulltext) < 10000 and len(fulltext.split()) < 1400 :
            passed = False
            return self._result(passed, message = self.failure_message)
        else:
            passed = True
            return self._result(passed)


        
