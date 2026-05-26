"""Result models returned by checks, including per-check data schemas."""

from typing import Optional
from pydantic import BaseModel


class CheckResult(BaseModel):
    check_name: str
    ok: bool
    message: Optional[str] = None  # 200 char max, includes disposition
    data: Optional[BaseModel] = None  # extra JSON data


# TODO remove
class AlwaysPassContentCheckData(BaseModel):
    info: str


# TODO remove
class AlwaysPassMetadataValidationData(BaseModel):
    info: str
