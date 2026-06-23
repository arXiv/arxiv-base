"""checksum for arXiv metadata for use with QA."""

import zlib

from qa.checks.models import MetadataProtocol

_DIVIDER = "𒑰"


def checksum_metadata(submission: MetadataProtocol) -> int:
    """
    Make a checksum using the fields of `MetadataProtocol`.
    'None' values are treated as an empty string.
    """
    value = (
        f"{submission.title or ''}{_DIVIDER}"
        f"{submission.authors or ''}{_DIVIDER}"
        f"{submission.abstract or ''}{_DIVIDER}"
        f"{submission.comments or ''}{_DIVIDER}"
        f"{submission.report_num or ''}{_DIVIDER}"
        f"{submission.journal_ref or ''}{_DIVIDER}"
        f"{submission.doi or ''}{_DIVIDER}"
        f"{submission.msc_class or ''}{_DIVIDER}"
        f"{submission.acm_class or ''}"
    )
    return zlib.adler32(value.encode("utf-8"))
