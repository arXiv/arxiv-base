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

from qa.checks.metadata.oversize import OversizeCheck  # noqa
from qa.checks.metadata.withdrawal import WithdrawalCheck  # noqa

from qa.checks.fulltext.extraction import TextExtractionSuccessful  # noqa
from qa.checks.fulltext.structure import FulltextNotTooShort  # noqa

submission_checks: list[BaseCheck] = [
    TitleIsValid(),
    AuthorsAreValid(),
    AbstractIsValid(),
    CommentsAreValid(),
    ReportNumIsValid(),
    JournalRefIsValid(),
    DoiIsValid(),
    MscClassIsValid(),
    AcmClassIsValid(),
    OversizeCheck(),
    WithdrawalCheck(),
]

fulltext_checks: list[BaseCheck] = [
    TextExtractionSuccessful(),
    FulltextNotTooShort(),
]

checks: list[BaseCheck] = submission_checks + fulltext_checks
