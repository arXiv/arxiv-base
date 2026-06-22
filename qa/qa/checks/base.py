"""Abstract base classes for all checks."""

from abc import ABC, abstractmethod
import re


from qa.checks.models import Result, Offset, OnFailurePolicy, Disposition, QaDataRegistry


class MissingDataError(Exception):
    pass


class EmptyFieldError(Exception):
    pass


class BaseCheck(ABC):
    """
    Raises a MissingDataError if any of the required data are missing.
    """

    name: str
    display_name: str
    id: int
    version: str
    description: str
    on_failure_policy: OnFailurePolicy
    failure_message: str

    required_data: set[str] = set()

    @property
    def config(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "id": self.id,
            "version": self.version,
            "required_data": self.required_data,
            "on_failure_policy": self.on_failure_policy,
            "failure_message": self.failure_message,
        }

    def _describe(self) -> dict:
        return {
            **self.config,
            "description": self.description,
        }

    def _validate_data(self, data_registry: QaDataRegistry) -> None:
        for d in self.required_data:
            if getattr(data_registry, d) is None:
                raise MissingDataError(f"Required data '{d}' is missing.")

    @abstractmethod
    def _run(self, data_registry: QaDataRegistry) -> Result:
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

    def run(self, data_registry: QaDataRegistry) -> Result:
        self._validate_data(data_registry)
        return self._run(data_registry)


class BaseGenericCheck(BaseCheck):
    """
    An extension of BaseCheck that can be instantiated to run on different fields with different on failure policies.
    Raises a MissingDataError if either the required data is missing or the field is empty.
    """

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
        self.required_data = {data}
        self.data = data
        self.field = field

    @property
    def config(self) -> dict:
        """
        Return instance-level configuration.
        """
        return {
            **super().config,
            "field": self.field,
        }

    def _validate_data(self, data_registry: QaDataRegistry) -> None:
        """Validate that the data and field are not missing or empty."""
        super()._validate_data(data_registry)

        if getattr(getattr(data_registry, self.data), self.field) in (None, ""):
            raise EmptyFieldError(f"Field {self.field} in required data '{self.data}' is empty.")

    @abstractmethod
    def _run(self, data_registry: QaDataRegistry) -> Result:
        pass


class BaseGenericPatternCheck(BaseGenericCheck):
    """An extension of BaseGenericCheck that applies a regex pattern (matches are failing)."""

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

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """The pattern applied to the configured field should not return any matches."""
        v = getattr(getattr(data_registry, self.data), self.field)

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
    """
    An extension of BaseCheck that runs many generic sub-checks.
    Raises a MissingDataError if any of the required data is missing.
    Returns a failure if a field required by a sub-check is empty.
    """

    _checks: tuple[BaseGenericCheck, ...]

    def _describe(self) -> dict:
        return {
            **super()._describe(),
            "checks": [c._describe() for c in self._checks],
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """Run all sub-checks and return results."""

        results: list[Result] = []

        for check in self._checks:
            try:
                result = check.run(data_registry)
                results.append(result)
            except EmptyFieldError:
                return self._result(passed=False, results=[], message=self.failure_message)

        if self._passed(results):
            return self._result(passed=True, results=results)
        else:
            return self._result(passed=False, results=results, message=self.failure_message)

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
