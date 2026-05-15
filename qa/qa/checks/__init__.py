"""QA checks package: exposes all checks and their input/output models."""

from qa.checks.base import BaseCheck  # noqa

import qa.checks.models  # noqa

from qa.checks.content import AlwaysPassContentCheck  # noqa
from qa.checks.metadata_validation import AlwaysPassMetadataValidationCheck  # noqa

checks: list[BaseCheck] = [
    AlwaysPassMetadataValidationCheck(),
    AlwaysPassContentCheck(),
]
