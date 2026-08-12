"""Generic URL and DOI checks."""

from qa.checks.models import Result, Offset, QaDataRegistry
from qa.checks.base import BaseGenericPatternCheck


class DoesNotContainUrl(BaseGenericPatternCheck):
    name = "does_not_contain_url"
    display_name = "Does Not Contain URL"
    id = 10039
    version = "1.0.0"
    description = "The value does not contain a URL."
    failure_message = "Contains a URL."

    _pattern = r"(?i)https?:"


class DoesNotContainDoi(BaseGenericPatternCheck):
    name = "does_not_contain_doi"
    display_name = "Does Not Contain DOI"
    id = 10045
    version = "1.0.0"
    description = "The value does not contain the word 'DOI'."
    failure_message = "Contains 'DOI'."

    _pattern = r"(?i)doi"


class DoesNotContainBareDoi(BaseGenericPatternCheck):
    name = "does_not_contain_bare_doi"
    display_name = "Does Not Contain Bare DOI"
    id = 10040
    version = "1.0.0"
    description = "The value does not contain a bare DOI number (e.g. 10.1234/abc)."
    failure_message = "Contains a DOI."

    _pattern = r"(?i)^[0-9][0-9].[0-9]+/[^ ]*$"


class DoesNotContainBadDoiPrefix(BaseGenericPatternCheck):
    name = "does_not_contain_bad_doi_prefix"
    display_name = "Does Not Contain Bad DOI Prefix"
    id = 10047
    version = "1.0.0"
    description = "The value does not begin with 'doi:', 'https://doi.org/', or similar URL prefixes."
    failure_message = "Contains unnecessary prefix."

    _pattern = r"(?i)^doi:|^https?://doi\.org/|^https?://.*\.doi\.org/"


class DoiHasValidFormat(BaseGenericPatternCheck):
    name = "doi_has_valid_format"
    display_name = "DOI Has Valid Format"
    id = 10050
    version = "1.0.0"
    description = "Each space-separated DOI in the value matches the expected DOI format."
    failure_message = "Invaleeid DOI."

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
