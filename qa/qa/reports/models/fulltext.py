"""Model for fulltext QA reports persisted to GCS."""

from typing import Literal

from qa.reports.models.base import BaseReport


class FulltextReport(BaseReport):
    name: str = "arXiv Fulltext Report"
    key_name: str = "fulltext"
    version: Literal["1.0"] = "1.0"
