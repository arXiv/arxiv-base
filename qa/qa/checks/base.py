"""Abstract base classes for all checks."""

from abc import ABC, abstractmethod
import re

from typing import Optional, Any

from qa.checks.models import Result, Offset, Disposition


class MissingDataError(Exception):
    pass


class BaseCheck(ABC):
    name: str
    id: int
    version: str
    description: str

    required_inputs: set[str] = set()
    failure_message: str

    disposition: Disposition

    def _validate_inputs(self, inputs: dict[str, Any]) -> None:
        """Validate required data are present."""
        for data in self.required_inputs:
            if data not in inputs or not inputs[data]:
                raise MissingDataError(f"Required data '{data}' is missing.")

    @abstractmethod
    def _run(self, inputs: dict[str, Any]) -> Result:
        pass

    def _result(
        self,
        passed: bool,
        message: str = "",
        offsets: Optional[list[Offset]] = None,
    ) -> Result:
        return Result(
            check_name=self.name,
            check_id=self.id,
            check_version=self.version,
            passed=passed,
            message=message,
            offsets=offsets,
        )

    def run(self, inputs: dict[str, Any]) -> Result:
        self._validate_inputs(inputs)
        return self._run(inputs)


class BaseGenericCheck(BaseCheck):
    def __init__(
        self,
        *,
        disposition: Disposition,
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

    def _validate_inputs(self, inputs: dict[str, Any]) -> None:
        super()._validate_inputs(inputs)
        if self.data not in inputs or not inputs[self.data]:
            raise MissingDataError(f"Required data '{self.data}' is missing.")

        v = getattr(inputs[self.data], self.field, None)
        if v is None:
            raise MissingDataError(f"Required field '{self.data}' '{self.field}' is missing.")

    @abstractmethod
    def _run(self, inputs: dict[str, Any]) -> Result:
        pass


class BaseGenericPatternCheck(BaseGenericCheck):
    _pattern: str

    def __init__(
        self,
        *,
        disposition: Disposition,
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

    def _run(self, inputs: dict[str, Any]) -> Result:
        """The pattern applied to the configured field should not return any matches."""
        v = getattr(inputs[self.data], self.field, None)

        offsets = []

        for match in self._compiled_pattern.finditer(v):
            offsets.append(Offset(start=match.start(), end=match.end()))

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
            "checks": [{"name": c.name, "id": c.id, "version": c.version, "config": c.config} for c in self._checks]
        }

    def _run(self, inputs: dict[str, Any]) -> Result:
        """Run all sub-checks and return results. If any sub-check fails and has a REJECT disposition, fail the aggregate check."""

        results: list[Result] = []
        passed = True

        for check in self._checks:
            result = check.run(inputs)
            results.append(result)

            if not result.passed and check.disposition == Disposition.REJECT:
                passed = False

        if passed:
            return Result(
                check_name=self.name,
                check_id=self.id,
                check_version=self.version,
                passed=True,
                message="",
                results=results,
            )
        else:
            return Result(
                check_name=self.name,
                check_id=self.id,
                check_version=self.version,
                passed=False,
                message="",  # TODO
                results=results,
            )
