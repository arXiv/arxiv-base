"""Generic DOI checks."""

from qa.checks.models import Result, Offset, QaDataRegistry
from qa.checks.base import BaseGenericPatternCheck


class DoiHasValidFormat(BaseGenericPatternCheck):
    name = "doi_has_valid_format"
    display_name = "DOI Has Valid Format"
    id = 10050
    version = "1.0.0"
    description = "Each space-separated DOI in the value matches the expected DOI format."
    failure_message = "Invalid DOI."

    _pattern = r"(?i)^(?![0-9][0-9]*\.[0-9][0-9]*/[A-Za-z0-9():;._/-]*$)"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)
        offsets = []
        start = 0
        for doi in v.split():
            idx = v.index(doi, start)
            end = idx + len(doi)
            if self._compiled_pattern.match(doi):
                offsets.append(Offset(start=idx, end=end))
            start = end
        if offsets:
            return self._result(passed=False, message=self.failure_message, offsets=offsets)
        return self._result(passed=True)
