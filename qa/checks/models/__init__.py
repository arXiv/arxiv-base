"""Input and output models for QA checks."""

from qa_checks.checks.models.inputs import CheckData, SubmissionMetadata
from qa_checks.checks.models.results import (
    CheckResult,
    AlwaysPassContentCheckReport,
    AlwaysPassMetadataValidationReport,
)
