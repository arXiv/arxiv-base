"""QA checks package: exposes all checks."""

from qa.checks.base import BaseCheck  # noqa
from qa.checks.metadata.abstract import AbstractIsValid  # noqa
from qa.checks.metadata.acm_class import AcmClassIsValid  # noqa
from qa.checks.metadata.authors import AuthorsAreValid  # noqa
from qa.checks.metadata.comments import CommentsAreValid  # noqa
from qa.checks.metadata.doi import DoiIsValid  # noqa
from qa.checks.metadata.journal_ref import JournalRefIsValid  # noqa
from qa.checks.metadata.msc_class import MscClassIsValid  # noqa
from qa.checks.metadata.report_num import ReportNumIsValid  # noqa
from qa.checks.metadata.title import TitleIsValid  # noqa

from qa.checks.fulltext.text_checks import MissingTextCheck, VeryShortTextCheck # noqa

checks: list[BaseCheck] = [
    TitleIsValid(),
    AuthorsAreValid(),
    AbstractIsValid(),
    CommentsAreValid(),
    ReportNumIsValid(),
    JournalRefIsValid(),
    DoiIsValid(),
    MscClassIsValid(),
    AcmClassIsValid(),
    MissingTextCheck(),
    VeryShortTextCheck(),
]
