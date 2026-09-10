"""Generic ACM class checks."""

from qa.checks.models import Result, Offset, QaDataRegistry
from qa.checks.base import BaseGenericPatternCheck


class AcmClassHasValidFormat(BaseGenericPatternCheck):
    name = "acm_class_has_valid_format"
    display_name = "ACM Class Has Valid Format"
    id = 10075
    version = "1.0.0"
    description = "Each semicolon-separated ACM class in the value matches the expected ACM classification format."
    failure_message = "Contains an ACM class that doesn't match the expected format (e.g. 'F.2.2' or 'I.2.7')."

    _pattern = r"^[A-K]\.[0-9m](\.(\d{1,2}|m)(\.[a-o])?)?$"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)
        offsets = []
        start = 0

        for acm_class in v.split(";"):
            idx = v.index(acm_class, start)
            end = idx + len(acm_class)
            if not self._compiled_pattern.match(acm_class.strip()):
                offsets.append(Offset(start=idx, end=end))
            start = end

        if offsets:
            return self._result(passed=False, message=self.failure_message, offsets=offsets)
        return self._result(passed=True)
