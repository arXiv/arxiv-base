"""Result models returned by checks, including per-check report schemas."""

from typing import Optional
from pydantic import BaseModel


class CheckResult(BaseModel):
    check_name: str
    ok: bool
    message: Optional[str] = None  # 200 char max, includes disposition
    data: Optional[BaseModel] = None  # extra JSON data


# TODO remove
class AlwaysPassContentCheckReport(BaseModel):
    info: str


# TODO remove
class AlwaysPassMetadataValidationReport(BaseModel):
    info: str
