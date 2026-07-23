"""Submission file checks."""

from qa.checks.base import BaseCheck
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result


class DoesNotExceedTheFileSizeLimit(BaseCheck):
    name = "does_not_exceed_the_file_size_limit"
    display_name = "Does Not Exceed the File Size Limit"
    id = 48
    version = "1.0.0"
    description = "The submission does not exceed the file size limit."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Submission exceeds the file size limit."

    required_data = {"submission_pubsub_info"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        assert data_registry.submission_pubsub_info is not None

        if data_registry.submission_pubsub_info.is_oversize:
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)


# TODO: add HTML file type check
# TODO: add TeX processing flag checks (post-exCITe)
