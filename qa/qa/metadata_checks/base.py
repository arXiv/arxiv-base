"""Abstract base classes for all checks."""

from abc import ABC, abstractmethod
import re

from typing import Optional, Any

from qa.metadata_checks import models


class MissingDataError(Exception):
    pass


class BaseCheck(ABC):
    name: str
    id: int
    version: str
    description: str

    required_inputs: set[str] = set()
    failure_message: str

    disposition: models.Disposition

    def run(self, inputs: dict[str, Any]) -> models.Result:
        """Validate required data keys are present, then execute."""
        for data in self.required_inputs:
            if data not in inputs or not inputs[data]:
                raise MissingDataError(f"Required data '{data}' is missing.")
        return self._run(inputs)

    @abstractmethod
    def _run(self, inputs: dict[str, Any]) -> models.Result:
        pass

    def _result(
        self,
        passed: bool,
        message: str = "",
        offsets: Optional[list[models.Offset]] = None,
    ) -> models.Result:
        return models.Result(
            check_name=self.name,
            check_id=self.id,
            check_version=self.version,
            passed=passed,
            message=message,
            offsets=offsets,
        )


class BaseGenericCheck(BaseCheck):
    def __init__(
        self,
        *,
        disposition: models.Disposition,
        data: str,
        field: str,
    ) -> None:
        """
        Set instance-level attributes.
        """
        super().__init__()
        self.disposition = disposition
        self.data = data
        self.field = field

    @property
    def config(self) -> dict:
        """
        Return instance-level configuration.
        """
        return {
            "disposition": self.disposition,
            "data": self.data,
            "field": self.field,
        }

    def run(self, inputs: dict[str, Any]) -> models.Result:
        super().run(inputs)
        v = getattr(inputs[self.data], self.field, None)

        if not v:
            raise MissingDataError(
                f"Required field '{self.data}' '{self.field}' is missing."
            )

        return self._run(inputs)


# add_complaints_matching
class BaseGenericPatternCheck(BaseGenericCheck):
    _pattern: str

    def __init__(
        self,
        *,
        disposition: models.Disposition,
        data: str,
        field: str,
    ) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self._compiled_pattern: re.Pattern = re.compile(self._pattern)

    @property
    def config(self) -> dict:
        return {
            "disposition": self.disposition,
            "data": self.data,
            "field": self.field,
            "pattern": self._pattern,
        }

    def _run(self, inputs: dict[str, Any]) -> models.Result:
        """The pattern applied to the configured field should not return any matches."""
        v = getattr(inputs[self.data], self.field, None)
        offsets = []

        for match in self._compiled_pattern.finditer(v):
            offsets.append(models.Offset(start=match.start(), end=match.end()))

        if len(offsets) == 0:
            return self._result(passed=True)
        else:
            return self._result(
                passed=False,
                message=self.failure_message,
                offsets=offsets,
            )


class BaseAggregateCheck(BaseCheck):
    _checks: tuple[BaseGenericCheck, ...]

    @property
    def config(self) -> dict:
        """Return sub-checks and their configurations for the registry endpoint."""
        return {
            "checks": [
                {"name": c.name, "id": c.id, "version": c.version, "config": c.config}
                for c in self._checks
            ]
        }

    def run(self, inputs: dict[str, Any]) -> models.Result:
        results: list[models.Result] = []
        passed = True

        for check in self._checks:
            results.append(check.run(inputs))

            # TODO: review
            if check.disposition == models.Disposition.REJECT:
                passed = False

        message = ""  # TODO

        return models.Result(
            check_name=self.name,
            check_id=self.id,
            check_version=self.version,
            passed=passed,
            message=message,
            results=results,
        )
