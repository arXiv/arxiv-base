"""QA checks package: exposes all checks."""

from qa.checks.base import BaseCheck  # noqa
from qa.checks.metadata.title import ValidTitleCheck  # noqa

checks: list[BaseCheck] = [
    ValidTitleCheck(),
]
