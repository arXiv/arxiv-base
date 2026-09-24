from qa.checks.base import BaseCheck

from qa.checks.models import FlaggedTermsReport, Offset, OnFailurePolicy, QaDataRegistry, Result


class NoFlaggedTerms(BaseCheck):
    name = "no_flagged_terms"
    display_name = "No Flagged Terms"
    id = 7
    version = "1.0.0"
    description = "No flagged terms (fka concerning words) were found in the metadata or full text."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Flagged terms found"

    required_data = {"flagged_terms_report"}

    @classmethod
    def check(cls, flagged_terms_report: FlaggedTermsReport) -> Result:
        return cls().run(QaDataRegistry(flagged_terms_report=flagged_terms_report))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        flagged_terms_report = data_registry.flagged_terms_report
        assert flagged_terms_report is not None

        matches = flagged_terms_report.data

        if not matches:
            return self._result(passed=True)

        # One entry per flagged term, in the order first found.
        terms: dict[int, str] = {}
        for m in matches:
            terms.setdefault(m.keywords_id, m.keywords_name or m.match.strip())

        # Offsets are into the text of each match's own field.
        offsets = [
            Offset(start=m.starts_at, end=m.ends_at)
            for m in matches
            if m.starts_at is not None and m.ends_at is not None
        ]

        return self._result(
            passed=False,
            message=f"{self.failure_message}: {', '.join(terms.values())}",
            offsets=offsets or None,
        )
