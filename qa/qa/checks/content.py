"""Placeholder content check that always passes."""

from qa.checks.base import BaseCheck
from qa.checks import models


# TODO remove
class AlwaysPassContentCheck(BaseCheck):
    name = "always_pass_content"
    version = "0.1.0"
    description = "Placeholder content check that always passes."

    required_data = {"fulltext"}
    results_model = models.AlwaysPassContentCheckReport

    def _run(self, data: models.CheckData) -> models.CheckResult:
        _ = len(data.fulltext)  # type: ignore  # validated by BaseCheck.run

        return models.CheckResult(
            check_name="always_pass_content",
            ok=True,
            message="OK (placeholder)",
            data=models.AlwaysPassContentCheckReport(info="it passed"),
        )
