"""Models for representing QA reports."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, Json, ValidationInfo

id_regex = "^[a-z0-9]+(-[a-z0-9]+)*$"
"""Regex for report types and flag ids"""


class Flag(BaseModel):
    id: str = Field(
        title="Flag id",
        description="TODO the id of the individual flag or of the category of flag?",
        examples=["tex-created-flag"],
        pattern=id_regex,
    )
    description: Optional[str]


class BaseReport(BaseModel):
    """BaseReport used for both SummaryReport and QAReport"""

    key_name: str = Field(
        title="Report Key Name",
        description="The abbreviated name of the report",
        examples=["arxiv-example-report"],
        pattern=id_regex,
    )
    version: str = Field(
        description="The version of the report schema. This is not the version of the subission metadata."
    )
    submission_id: int = Field(gt=0)
    created: str = Field(default_factory=datetime.now(timezone.utc).isoformat)


class QAReport(BaseReport):
    flags: List[Flag] = []
    qa_exec_time_sec: Optional[int] = Field(
        default=None,
        description="Time it took to complete the QA check(s) for this report, in seconds.",
        ge=0,
    )
    data: dict


class Report(QAReport):
    name: str = Field(title="Report Name", description="The full name of the report")


class TEIAnalysisReport(Report):
    name: str = "arXiv TEI Analysis"
    key_name: str = "tei-analysis"


class KeywordSearchReport(Report):
    name: str = "arXiv Fulltext Keyword Search Report"
    key_name: str = "fulltext-keywords"


class AuthorCheckReport(Report):
    name: str = "arXiv Author Metadata Report"
    key_name: str = "author-check"


class FulltextReport(Report):
    name: str = "arXiv Fulltext Report"
    key_name: str = "fulltext"


class OverlapReport(Report):
    name: str = "arXiv Overlap Report"
    key_name: str = "overlap"


class PDFInfoReport(Report):
    name: str = "arXiv PDFInfo Report"
    key_name: str = "pdfinfo"


class TeXWrappedReport(Report):
    name: str = "arXiv TeX Wrapped Report"
    key_name: str = "tex-wrapped"


class TeXCreatedReport(Report):
    name: str = "arXiv TeX Created Report"
    key_name: str = "tex-created"


class SummaryReport(BaseReport):
    name: str = "arXiv Submission QA Summary Report"
    key_name: str = "qa-summary"
    version: str = "1.0"
    reports: List[Report] = []
    flagged_keys: Optional[List[str]] = []
    missing_keys: Optional[List[str]] = []

    @field_validator("flagged_keys")
    def flagged_keys_match_reports(cls, v: List[str], info: ValidationInfo):
        reports = info.data.get("reports", [])

        if len(v) > 0:
            for key in v:
                found_key = False
                for report in reports:
                    if key == report.key_name:
                        found_key = True
                        if len(report.flags) == 0:
                            raise ValueError(
                                "expect at find least 1 flag in flagged report"
                            )
                        continue
                if not found_key:
                    raise ValueError("report key not found in reports")


class SubmissionQAReport(BaseModel):
    id: int
    submission_id: int
    key_name: str = Field(max_length=64)
    created: Optional[datetime]
    num_flags: int
    report: Json[dict]
    uri: Optional[str] = Field(default=None, max_length=256)

    model_config = ConfigDict(from_attributes=True)
