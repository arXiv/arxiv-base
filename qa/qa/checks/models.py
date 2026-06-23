from pydantic import BaseModel
from typing import Protocol, runtime_checkable
from enum import StrEnum


class OnFailurePolicy(StrEnum):
    """
    The on failure policy describes how to handle a failure (non-passing result) from a particular check.
    Each instance of a check should be configured with only one on failure policy.

    IGNORE - failure should be ignored
    WARN - failure should elicit a non-blocking warning
    REJECT - failure should be a blocking error
    """

    IGNORE = "ignore"
    WARN = "warn"
    REJECT = "reject"


class Disposition(StrEnum):
    """
    The disposition represents the end state of running a check.
    It rationalizes a passing/non-passing result against that check's on failure policy.
    All passing check results will provide a disposition of "ok".
    """

    OK = "ok"
    WARN = "warn"
    REJECT = "reject"


class Offset(BaseModel):
    """A character-level span within a string."""

    start: int
    end: int


class Result(BaseModel):
    """
    A domain model representing a check result.
    Every failure (non-passing result) will include offsets.
    Every aggregate check result will include a list of results from sub-checks.
    """

    check_config: dict
    passed: bool
    disposition: Disposition
    message: str
    offsets: list[Offset] | None = None
    results: list["Result"] | None = None


class SubmissionMetadata(BaseModel):
    """
    Information about a submission.
    This should be a concrete implementation of MetadataProtocol for use in checks.
    """

     # MetadataProtocol fields     
    title: str | None = None
    authors: str | None = None
    abstract: str | None = None
    comments: str | None = None
    report_num: str | None = None
    journal_ref: str | None = None
    doi: str | None = None
    msc_class: str | None = None
    acm_class: str | None = None
    # End MetadataProtocol fields
    type: str | None = None # one of: "new", "rep", "wdr", "jref", or "cross"
    is_overlap: bool = False
    data_version: int = 0
    metadata_version: int = 0

@runtime_checkable
class MetadataProtocol(Protocol):
    """
    A protocol representing the shape of submission metadata.
    Only enforces attribute presence.
    Can be used with any object.
    """

    title: str | None
    authors: str | None
    abstract: str | None
    comments: str | None
    report_num: str | None
    journal_ref: str | None
    doi: str | None
    msc_class: str | None
    acm_class: str | None


class QaDataRegistry(BaseModel):
    """Data dependencies for checks."""

    fulltext: str | None = None
    fulltext_report: str | None = None
    author_report: str | None = None
    flagged_terms_report: str | None = None
    tex_report: str | None = None
    metadata: SubmissionMetadata | None = None
