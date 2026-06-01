"""Base model for QA reports persisted to storage."""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional

kebab_case = "^[a-z0-9]+(-[a-z0-9]+)*$"


class Flag(BaseModel):
    id: str = Field(
        description="TODO the id of the individual flag or of the category of flag?",
        examples=["tex-created-flag"],
        pattern=kebab_case,
    )
    description: Optional[str]


class BaseReport(BaseModel):
    name: str = Field(description="The full name of the report.")
    key_name: str = Field(
        description="The abbreviated name of the report.",
        examples=["arxiv-example-report"],
        pattern=kebab_case,
    )
    version: str = Field(description="The semantic version of the report schema.")
    submission_id: int = Field(gt=0)
    created: str = Field(
        description="The timestamp representing when the report was created.",
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    flags: List[Flag] = []
    qa_exec_time_sec: Optional[int] = Field(
        default=None,
        description="Time it took to process and generate the report, in seconds.",
        ge=0,
    )
    data: dict
