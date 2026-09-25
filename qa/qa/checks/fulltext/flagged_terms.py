from qa.checks import generic
from qa.checks.base import BaseAggregateCheck
from qa.checks.generic.flagged_terms import flagged_terms
from qa.checks.models import Disposition, FlaggedTermsReport, OnFailurePolicy, QaDataRegistry, Result

# The fields searched by the concerning_words cloud function
FLAGGED_TERMS_FIELDS = ("title", "authors", "abstract", "comments", "journal_ref", "fulltext")


class NoFlaggedTerms(BaseAggregateCheck):
    """Aggregate check with one sub-check per field."""

    name = "no_flagged_terms"
    display_name = "No Flagged Terms"
    id = 7
    version = "1.0.0"
    description = "No flagged terms were found in the metadata or fulltext."
    failure_message = "Flagged terms found"

    required_data = {"flagged_terms_report"}

    _checks = tuple(
        generic.DoesNotContainFlaggedTerms(
            on_failure_policy=OnFailurePolicy.WARN, data="flagged_terms_report", field=field
        )
        for field in FLAGGED_TERMS_FIELDS
    )

    @classmethod
    def check(cls, flagged_terms_report: FlaggedTermsReport) -> Result:
        return cls().run(QaDataRegistry(flagged_terms_report=flagged_terms_report))

    def _run(self, data_registry: QaDataRegistry) -> Result:
        result = super()._run(data_registry)

        if result.disposition != Disposition.OK:
            report = data_registry.flagged_terms_report
            assert report is not None

            matches = [m for m in report.data if m.field in FLAGGED_TERMS_FIELDS]
            result.message = f"{self.failure_message}: {', '.join(flagged_terms(matches))}"

        return result
