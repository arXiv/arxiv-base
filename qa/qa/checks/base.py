"""Abstract base classes for all checks."""

from abc import ABC, abstractmethod
import re


from qa.checks.models import Result, Offset, OnFailurePolicy, Inputs, Disposition


class MissingDataError(Exception):
    pass


class BaseCheck(ABC):
    name: str
    display_name: str
    id: int
    version: str
    description: str
    on_failure_policy: OnFailurePolicy
    failure_message: str

    required_inputs: set[str] = set()

    @property
    def config(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "id": self.id,
            "version": self.version,
            "on_failure_policy": self.on_failure_policy,
            "failure_message": self.failure_message,
        }

    def _describe(self) -> dict:
        return {
            **self.config,
            "description": self.description,
            "required_inputs": self.required_inputs,
        }

    def _validate_inputs(self, inputs: Inputs) -> None:
        for data in self.required_inputs:
            if getattr(inputs, data) is None:
                raise MissingDataError(f"Required data '{data}' is missing.")

    @abstractmethod
    def _run(self, inputs: Inputs) -> Result:
        pass

    def _disposition(self, passed: bool) -> Disposition:
        if passed or self.on_failure_policy == OnFailurePolicy.IGNORE:
            return Disposition.OK
        if self.on_failure_policy == OnFailurePolicy.WARN:
            return Disposition.WARN
        return Disposition.REJECT

    def _result(
        self,
        passed: bool,
        message: str = "",
        offsets: list[Offset] | None = None,
    ) -> Result:
        return Result(
            check_config=self.config,
            passed=passed,
            disposition=self._disposition(passed),
            message=message,
            offsets=offsets,
        )

    def run(self, inputs: Inputs) -> Result:
        self._validate_inputs(inputs)
        return self._run(inputs)


class BaseGenericCheck(BaseCheck):
    """A check that can be instantiated to run on different fields with different on failure policies."""

    def __init__(
        self,
        *,
        on_failure_policy: OnFailurePolicy,
        data: str,
        field: str,
    ) -> None:
        """
        Set instance-level attributes.
        """
        super().__init__()
        self.on_failure_policy = on_failure_policy
        self.data = data
        self.field = field

    @property
    def config(self) -> dict:
        """
        Return instance-level configuration.
        """
        return {
            **super().config,
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
        on_failure_policy: OnFailurePolicy,
        data: str,
        field: str,
    ) -> None:
        super().__init__(on_failure_policy=on_failure_policy, data=data, field=field)
        self._compiled_pattern: re.Pattern = re.compile(self._pattern)

    @property
    def config(self) -> dict:
        return {
            **super().config,
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

    def _describe(self) -> dict:
        return {
            **super()._describe(),
            "checks": [c._describe() for c in self._checks],
        }

    def _run(self, inputs: Inputs) -> Result:
        """Run all sub-checks and return results."""

        results: list[Result] = []

        for check in self._checks:
            result = check.run(inputs)
            results.append(result)

        passed = self._passed(results)
        return self._result(passed=passed, results=results)

    def _passed(self, results: list[Result]) -> bool:
        """The aggregate passes unless a sub-check with REJECT policy has failed."""
        return not any(not r.passed and r.check_config["on_failure_policy"] == OnFailurePolicy.REJECT for r in results)

    def _result(  # type: ignore
        self,
        passed: bool,
        results: list[Result],
        message: str = "",
    ) -> Result:
        return Result(
            check_config=self.config,
            passed=passed,
            disposition=self._disposition(passed),
            message=message,
            results=results,
        )
