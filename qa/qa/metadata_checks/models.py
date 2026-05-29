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


class Offset(BaseModel):
    """A character-level span within a string."""

    start: int
    end: int


class Result(BaseModel):
    """
    An internal (domain) model representing a check result, both passing and non-passing.
    Every failure (non-passing result) will include offsets.
    Every aggregate check result will include a list of results from sub-checks.
    """

    check_name: str
    check_id: int
    check_version: str
    passed: bool
    message: str
    offsets: Optional[list[Offset]] = None
    results: Optional[list["Result"]] = None
