"""Abstract class for checks"""

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel

from qa_checks.checks import models


class MissingDataError(Exception):
    pass


class BaseCheck(ABC):
    name: ClassVar[str]
    version: ClassVar[str]
    description: ClassVar[str]

    required_data: ClassVar[set[str]] = set()
    results_model: ClassVar[type[BaseModel]]

    enabled: ClassVar[bool] = True

    def run(self, data: models.CheckData) -> models.CheckResult:
        """Validate required data fields are present, then execute the check."""
        for field in self.required_data:
            if getattr(data, field) is None:
                raise MissingDataError(f"Required field '{field}' is missing")
        return self._run(data)

    @abstractmethod
    def _run(self, data: models.CheckData) -> models.CheckResult:
        pass
