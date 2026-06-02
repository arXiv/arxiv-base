"""QA checks package: exposes all checks."""

from qa.checks.base import BaseCheck  # noqa
from qa.checks.metadata.abstract import AbstractIsValid  # noqa
from qa.checks.metadata.authors import AuthorsAreValid  # noqa
from qa.checks.metadata.title import TitleIsValid  # noqa

checks: list[BaseCheck] = [
    TitleIsValid(),
    AuthorsAreValid(),
    AbstractIsValid(),
]
