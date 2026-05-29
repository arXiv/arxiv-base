"""Shared data models for the QA check system."""

from typing import Optional
from enum import StrEnum

from pydantic import BaseModel


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


class Offset(BaseModel):  # TODO
    """A character-level span within a string."""

    start: int
    end: int
    excerpt: str = ""


class Result(BaseModel):
    check_name: str
    check_id: int
    check_version: str
    passed: bool
    message: str
    offsets: Optional[list[Offset]] = None
    results: Optional[list["Result"]] = None
