"""Abstract base classes for all checks."""

from abc import ABC, abstractmethod
import re


from qa.checks.models import Result, Offset, Disposition, Inputs


class MissingDataError(Exception):
    pass


class BaseCheck(ABC):
    name: str
    id: int
    version: str
    description: str
    failure_message: str

    disposition: Disposition
    required_inputs: set[str] = set()

    def _validate_inputs(self, inputs: Inputs) -> None:
        for data in self.required_inputs:
            if getattr(inputs, data) is None:
                raise MissingDataError(f"Required data '{data}' is missing.")

    @abstractmethod
    def _run(self, inputs: Inputs) -> Result:
        pass

    def _result(
        self,
        passed: bool,
        message: str = "",
        offsets: list[Offset] | None = None,
    ) -> Result:
        return Result(
            check_name=self.name,
            check_id=self.id,
            check_version=self.version,
            passed=passed,
            disposition=self.disposition,
            message=message,
            offsets=offsets,
        )

    def run(self, inputs: Inputs) -> Result:
        self._validate_inputs(inputs)
        return self._run(inputs)


class BaseGenericCheck(BaseCheck):
    """A check that can be instantiated to run on different fields with different dispositions."""

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

    def _validate_inputs(self, inputs: Inputs) -> None:
        super()._validate_inputs(inputs)
        if getattr(inputs, self.data) is None:
            raise MissingDataError(f"Required data '{self.data}' is missing.")

        if getattr(getattr(inputs, self.data), self.field, None) is None:
            raise MissingDataError(f"Required field '{self.data}' '{self.field}' is missing.")

    @abstractmethod
    def _run(self, inputs: Inputs) -> Result:
        pass


class BaseGenericPatternCheck(BaseGenericCheck):
    """A generic check that applies a regex pattern (matches are failing)."""

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

    def _run(self, inputs: Inputs) -> Result:
        """The pattern applied to the configured field should not return any matches."""
        v = getattr(getattr(inputs, self.data), self.field)

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
    """A check that comprises many generic sub-checks."""

    _checks: tuple[BaseGenericCheck, ...]
    disposition: Disposition = Disposition.REJECT

    @property
    def config(self) -> dict:
        """Return sub-checks and their configurations for the registry endpoint."""
        return {
            "checks": [{"name": c.name, "id": c.id, "version": c.version, "config": c.config} for c in self._checks]
        }

    def _run(self, inputs: Inputs) -> Result:
        """Run all sub-checks and return results. If any sub-check fails and has a REJECT disposition, fail the aggregate check."""

        results: list[Result] = []
        passed = True

        for check in self._checks:
            result = check.run(inputs)
            results.append(result)

            if not result.passed and check.disposition == Disposition.REJECT:
                passed = False

        return Result(
            check_name=self.name,
            check_id=self.id,
            check_version=self.version,
            passed=passed,
            disposition=self.disposition,
            message="",
            results=results,
        )
