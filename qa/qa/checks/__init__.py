"""QA checks package: exposes all checks."""

from qa.checks.base import BaseCheck, BaseMetadataAggregateCheck  # noqa
from qa.checks.metadata.abstract import AbstractIsValid  # noqa
from qa.checks.metadata.acm_class import AcmClassIsValid  # noqa
from qa.checks.metadata.authors import AuthorsAreValid  # noqa
from qa.checks.metadata.comments import CommentsAreValid  # noqa
from qa.checks.metadata.doi import DoiIsValid  # noqa
from qa.checks.metadata.journal_ref import JournalRefIsValid  # noqa
from qa.checks.metadata.msc_class import MscClassIsValid  # noqa
from qa.checks.metadata.report_num import ReportNumIsValid  # noqa
from qa.checks.metadata.title import TitleIsValid  # noqa

from qa.checks.submission.files import DoesNotExceedTheFileSizeLimit, FileTypeDoesNotRequireReview  # noqa
from qa.checks.submission.type import IsNotAWithdrawal  # noqa
from qa.checks.submission.user import AuthorsContainsSubmitterName, SubmitterIsNotFlagged  # noqa

from qa.checks.fulltext.authors import AuthorsFoundInFulltext  # noqa
from qa.checks.fulltext.extraction import TextExtractionSuccessful  # noqa
from qa.checks.fulltext.flagged_terms import NoFlaggedTerms  # noqa
from qa.checks.fulltext.language import FulltextHasEnoughEnglish, FulltextLanguageRecognized  # noqa
from qa.checks.fulltext.structure import FulltextNotTooShort  # noqa

# Checks on a single metadata field, runnable with metadata alone. Callers key
# results by each check's `field`, so checks across fields or needing other data
# belong in submit_event_checks.
metadata_checks: list[BaseMetadataAggregateCheck] = [
    TitleIsValid(),
    AuthorsAreValid(),
    AbstractIsValid(),
    CommentsAreValid(),
    ReportNumIsValid(),
    JournalRefIsValid(),
    DoiIsValid(),
    MscClassIsValid(),
    AcmClassIsValid(),
]

submit_event_checks: list[BaseCheck] = [
    *metadata_checks,
    AuthorsContainsSubmitterName(),
    DoesNotExceedTheFileSizeLimit(),
    FileTypeDoesNotRequireReview(),
    IsNotAWithdrawal(),
    SubmitterIsNotFlagged(),
]

fulltext_checks: list[BaseCheck] = [
    TextExtractionSuccessful(),
    FulltextNotTooShort(),
    NoFlaggedTerms(),
    AuthorsFoundInFulltext(),
    FulltextLanguageRecognized(),
    FulltextHasEnoughEnglish(),
]

checks: list[BaseCheck] = submit_event_checks + fulltext_checks
