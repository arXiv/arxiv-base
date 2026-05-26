"""Input models passed to checks at execution time."""

from typing import Optional
from pydantic import BaseModel


class SubmissionMetadata(
    BaseModel
):  # TODO can we just extend or filter the submission table schema?
    """QA-relevant submission metadata"""

    type: Optional[str] = None  # "new", "rep", "wdr", "jref", "cross"
    sword_id: Optional[int] = None
    doc_paper_id: Optional[str] = None  # previous id for replacements
    authors: Optional[str] = None  # metacheck field
    primary_category: Optional[str] = None
    title: Optional[str] = None  # metacheck field
    abstract: Optional[str] = None  # metacheck field
    comments: Optional[str] = None  # metacheck field
    report_num: Optional[str] = None  # metacheck field
    journal_ref: Optional[str] = None  # metacheck field
    doi: Optional[str] = None  # metacheck field
    msc_class: Optional[str] = None  # metacheck field
    acm_class: Optional[str] = None  # metacheck field


class CheckData(BaseModel):
    """Data dependencies for checks"""

    fulltext: Optional[str] = None
    fulltext_report: Optional[str] = None
    author_report: Optional[str] = None
    flagged_terms_report: Optional[str] = None
    tex_report: Optional[str] = None
    metadata: Optional[SubmissionMetadata] = None
