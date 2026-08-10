from pydantic import BaseModel, Field
from typing import Literal, Protocol, runtime_checkable
from enum import StrEnum
from datetime import datetime, timezone

kebab_case = "^[a-z0-9]+(-[a-z0-9]+)*$"


class OnFailurePolicy(StrEnum):
    """
    The on failure policy is an attribute of a check. It is part of that check's configuration.
    It describes how to handle a failure (non-passing result) from that check.
    Each instance of a check should be configured with only one on failure policy.

    IGNORE - failure should be ignored
    WARN - failure should not block but prompt a warning or review
    REJECT - failure should block further progression
    """

    IGNORE = "ignore"
    WARN = "warn"
    REJECT = "reject"


class Disposition(StrEnum):
    """
    A disposition is an attribute of a check result. It represents the end state of running a check on a particular input.
    It is the rationalization of the result (passing/non-passing) against that check's on failure policy.
    All passing check results will provide a disposition of "ok".
    The disposition should be used by consumers of check results to guide next steps.
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

    def failure_messages(self, *dispositions: Disposition) -> str:
        """Return a concatenated string containing all messages for failed results with the given dispositions."""
        if not self.results:
            return self.message if not self.passed else ""
        return "\n".join(r.message for r in self.results if not r.passed and r.disposition in dispositions)


class Flag(BaseModel):
    id: str = Field(pattern=kebab_case)
    description: str | None


class BaseReport(BaseModel):
    name: str
    key_name: str = Field(pattern=kebab_case)
    version: str
    submission_id: int = Field(gt=0)
    created: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    flags: list[Flag] = []
    qa_exec_time_sec: int | None = Field(default=None, ge=0)
    data: dict


class FulltextReport(BaseReport):
    name: str = "arXiv Fulltext Report"
    key_name: str = "fulltext"
    version: str = "1.0"


class SubmitEventInfo(BaseModel):
    """Information about the submission."""

    type: Literal["new", "rep", "wdr", "jref", "cross"]
    is_oversize: bool
    submitter_name: str
    source_format: Literal["pdf", "tex", "pdftex", "withdrawn", "docx", "invalid", "ps", "html"]


class Metadata(BaseModel):
    """
    Paper metadata.
    """

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


class QaDataRegistry(BaseModel):
    """Data dependencies for checks."""

    fulltext: str | None = None
    fulltext_report: FulltextReport | None = None
    author_report: str | None = None
    flagged_terms_report: str | None = None
    tex_report: str | None = None
    metadata: Metadata | None = None
    submit_event_info: SubmitEventInfo | None = None
