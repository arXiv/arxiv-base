"""Submission file checks."""

from qa.checks.base import BaseCheck
from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result

# TODO: oversize images, too!


class DoesNotExceedTheFileSizeLimit(BaseCheck):
    name = "does_not_exceed_the_file_size_limit"
    display_name = "Does Not Exceed the File Size Limit"
    id = 48
    version = "1.0.0"
    description = "The submission does not exceed the file size limit."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Submission exceeds the file size limit."

    required_data = {"submit_event_info"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        assert data_registry.submit_event_info is not None

        if data_registry.submit_event_info.is_oversize:
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)


class FileTypeDoesNotRequireReview(BaseCheck):
    name = "acceptable_file_type"
    display_name = "Acceptable File type"
    id = 50
    version = "1.0.0"
    description = "The submission file type does not require manual review."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Submission file type requires manual review."

    required_data = {"submit_event_info"}

    def _run(self, data_registry: QaDataRegistry) -> Result:
        assert data_registry.submit_event_info is not None

        file_types_to_review = ["html",]

        if data_registry.submit_event_info.source_format in file_types_to_review:
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)


# TODO: add TeX processing flag checks (post-exCITe)
