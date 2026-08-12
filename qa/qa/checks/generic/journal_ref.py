"""Generic journal-ref specific checks."""

import re

from qa.checks.models import Result, Offset, QaDataRegistry
from qa.checks.base import BaseGenericCheck


class JournalRefIsWellFormed(BaseGenericCheck):
    name = "journal_ref_is_well_formed"
    display_name = "Journal Ref Is Well Formed"
    id = 10063
    version = "1.0.0"
    description = (
        "The value is 240 characters or fewer, does not contain 'submit', 'in press', 'appear', "
        "'accept', or 'to be publ' (which belong in Comments instead), and contains a valid "
        "4-digit year (19xx or 20xx)."
    )
    failure_message = "Not a well-formed journal reference."

    _max_chars = 240
    _forbidden_pattern = re.compile(r"(?i)submit|in press|appear|accept|to be publ")
    _year_pattern = re.compile(r"\b(?:19|20)\d{2}\b")

    def _run(self, data_registry: QaDataRegistry) -> Result:
        v = getattr(getattr(data_registry, self.data), self.field)

        offsets = []

        if len(v) > self._max_chars:
            offsets.append(Offset(start=self._max_chars, end=len(v)))

        forbidden_match = self._forbidden_pattern.search(v)
        if forbidden_match:
            offsets.append(Offset(start=forbidden_match.start(), end=forbidden_match.end()))

        if not self._year_pattern.search(v):
            offsets.append(Offset(start=0, end=len(v)))

        if offsets:
            return self._result(passed=False, message=self.failure_message, offsets=offsets)
        return self._result(passed=True)
