"""QA checks package: exposes all checks."""

from qa.checks.base import BaseCheck  # noqa
from qa.checks.metadata.abstract import AbstractIsValid  # noqa
from qa.checks.metadata.acm_class import AcmClassIsValid  # noqa
from qa.checks.metadata.authors import AuthorsAreValid, AuthorsContainsSubmitterName  # noqa
from qa.checks.metadata.comments import CommentsAreValid  # noqa
from qa.checks.metadata.doi import DoiIsValid  # noqa
from qa.checks.metadata.journal_ref import JournalRefIsValid  # noqa
from qa.checks.metadata.msc_class import MscClassIsValid  # noqa
from qa.checks.metadata.report_num import ReportNumIsValid  # noqa
from qa.checks.metadata.title import TitleIsValid  # noqa

from qa.checks.submission.files import DoesNotExceedTheFileSizeLimit, FileTypeDoesNotRequireReview  # noqa
from qa.checks.submission.type import IsNotAWithdrawal  # noqa

from qa.checks.fulltext.extraction import TextExtractionSuccessful  # noqa
from qa.checks.fulltext.structure import FulltextNotTooShort  # noqa

submit_event_checks: list[BaseCheck] = [
    TitleIsValid(),
    AuthorsAreValid(),
    AuthorsContainsSubmitterName(),
    AbstractIsValid(),
    CommentsAreValid(),
    ReportNumIsValid(),
    JournalRefIsValid(),
    DoiIsValid(),
    MscClassIsValid(),
    AcmClassIsValid(),
    DoesNotExceedTheFileSizeLimit(),
    FileTypeDoesNotRequireReview(),
    IsNotAWithdrawal(),
]

fulltext_checks: list[BaseCheck] = [
    TextExtractionSuccessful(),
    FulltextNotTooShort(),
]

checks: list[BaseCheck] = submit_event_checks + fulltext_checks
