"""Generic DOI checks."""

from qa.checks.models import Result, Offset, QaDataRegistry
from qa.checks.base import BaseGenericPatternCheck


class DoiHasValidFormat(BaseGenericPatternCheck):
    name = "doi_has_valid_format"
    display_name = "DOI Has Valid Format"
    id = 10050
    version = "1.0.0"
    description = "Each space-separated DOI in the value matches the expected DOI format."
    failure_message = failure_message = (
        "Contains a DOI that doesn't match the expected format: digits, followed by a period, followed by '/' and a suffix (e.g. '10.1234/abc123')."
    )

    _pattern = r"[0-9]+(\.[0-9]+)/.*"

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
