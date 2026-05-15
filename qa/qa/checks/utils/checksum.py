"""checksum for arXiv metadata for use with QA."""

import zlib

from arxiv.metadata import MetadataProtocol

_DIVIDER = "𒑰"


def checksum_metadata(submission: MetadataProtocol) -> int:
    """Make a checksum using the fields of `MetadataProtocol`.

    If this is the only function used from arxiv-base it can be installed
    without other dependenices.
    """
    value = (
        f"{submission.title}{_DIVIDER}"
        f"{submission.authors}{_DIVIDER}"
        f"{submission.abstract}{_DIVIDER}"
        f"{submission.comments}{_DIVIDER}"
        f"{submission.report_num}{_DIVIDER}"
        f"{submission.journal_ref}{_DIVIDER}"
        f"{submission.doi}{_DIVIDER}"
        f"{submission.msc_class}{_DIVIDER}"
        f"{submission.acm_class}"
    )
    return zlib.adler32(value.encode("utf-8"))
