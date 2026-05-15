"""QA checks package: exposes all checks and their input/output models."""

from qa_checks.checks.base import BaseCheck

import qa_checks.checks.models

from qa_checks.checks.content import AlwaysPassContentCheck
from qa_checks.checks.metadata_validation import AlwaysPassMetadataValidationCheck

checks: list[BaseCheck] = [
    AlwaysPassMetadataValidationCheck(),
    AlwaysPassContentCheck(),
]
