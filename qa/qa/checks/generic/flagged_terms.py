from qa.checks.base import BaseGenericCheck
from qa.checks.models import FlaggedTermMatch, FlaggedTermsReport, Offset, QaDataRegistry, Result


def flagged_terms(matches: list[FlaggedTermMatch]) -> list[str]:
    """One entry per flagged term, in the order first found."""
    terms: dict[int, str] = {}

    for m in matches:
        terms.setdefault(m.keywords_id, m.keywords_name or m.match.strip())

    return list(terms.values())


class DoesNotContainFlaggedTerms(BaseGenericCheck):
    """
    Reads the flagged terms report rather than the value itself: `field` is the report's name for the
    searched text (e.g. "title", "fulltext"), and `data` is the registry key of the report.
    """

    name = "does_not_contain_flagged_terms"
    display_name = "Does Not Contain Flagged Terms"
    id = 10076
    version = "1.0.0"
    description = "The flagged terms report has no matches in the value."
    failure_message = "Flagged terms found"

    def _run(self, data_registry: QaDataRegistry) -> Result:
        report: FlaggedTermsReport = getattr(data_registry, self.data)
        assert report is not None

        matches = [m for m in report.data if m.field == self.field]

        if not matches:
            return self._result(passed=True)

        # Offsets are into the text of self.field.
        offsets = [
            Offset(start=m.starts_at, end=m.ends_at)
            for m in matches
            if m.starts_at is not None and m.ends_at is not None
        ]

        return self._result(
            passed=False,
            message=f"{self.failure_message}: {', '.join(flagged_terms(matches))}",
            offsets=offsets or None,
        )
