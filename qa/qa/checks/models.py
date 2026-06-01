from pydantic import BaseModel
from typing import Protocol, runtime_checkable
from enum import StrEnum


class Disposition(StrEnum):
    """
    The disposition for a check indicates how a failure (non-passing result) should be treated.
    Each instance of a check should be configured with only one disposition.

    OK - failure is ignored, treated as OK
    WARN - failure is a non-blocking warning
    REJECT - failure is a blocking error

    Success (a passing result) always produces OK regardless of that check's configured disposition.
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

    check_name: str
    check_id: int
    check_version: str
    passed: bool
    message: str
    offsets: list[Offset] | None = None
    results: list["Result"] | None = None


class Metadata(BaseModel):
    """A concrete implementation of MetadataProtocol for use in checks."""

    title: str | None = None
    authors: str | None = None
    abstract: str | None = None
    comments: str | None = None
    report_num: str | None = None
    journal_ref: str | None = None
    doi: str | None = None
    msc_class: str | None = None
    acm_class: str | None = None


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


class CheckData(BaseModel):
    """Data dependencies for checks."""

    fulltext: str | None = None
    fulltext_report: str | None = None
    author_report: str | None = None
    flagged_terms_report: str | None = None
    tex_report: str | None = None
    metadata: Metadata | None = None
