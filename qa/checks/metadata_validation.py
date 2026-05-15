"""Placeholder metadata validation check that always passes."""

from qa_checks.checks.base import BaseCheck
from qa_checks.checks import models


# TODO remove
class AlwaysPassMetadataValidationCheck(BaseCheck):
    name = "always_pass_metadata_validation"
    version = "0.1.0"
    description = "Placeholder metadata validation check that always passes."

    required_data = {"metadata"}
    results_model = models.AlwaysPassMetadataValidationReport

    def _run(self, data: models.CheckData) -> models.CheckResult:
        _ = data.metadata.title  # type: ignore[union-attr]  # validated by BaseCheck.run

        return models.CheckResult(
            check_name="always_pass_metadata_validation",
            ok=True,
            message="OK (placeholder)",
            data=models.AlwaysPassMetadataValidationReport(info="it passed"),
        )
