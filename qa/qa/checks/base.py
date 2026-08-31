"""Abstract base classes for all checks."""

from abc import ABC, abstractmethod
import re


from qa.checks.models import Result, Offset, OnFailurePolicy, Disposition, QaDataRegistry, Metadata


class MissingDataError(Exception):
    """A required data object in the QaDataRegistry (e.g. Metadata) is None."""

    pass


class EmptyFieldError(Exception):
    """A required field (e.g. Metadata.title) is None or an empty string."""

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
    Raises a MissingDataError if any of the required data are missing.
    """
    _short_circuits_on_failure: bool = False

    def __init__(
        self,
        *,
        on_failure_policy: OnFailurePolicy,
        data: str,
        field: str,
        failure_message: str | None = None,
    ) -> None:
        """
        Set instance-level attributes.
        """
        super().__init__()
        self.on_failure_policy = on_failure_policy
        self.required_data = {data}
        self.data = data
        self.field = field
        if failure_message is not None:
            self.failure_message = failure_message

    @property
    def config(self) -> dict:
        """
        Return instance-level configuration.
        """
        return {
            **super().config,
            "field": self.field,
        }

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
        failure_message: str | None = None,
    ) -> None:
        super().__init__(on_failure_policy=on_failure_policy, data=data, field=field, failure_message=failure_message)
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
    """An extension of BaseCheck that runs many generic sub-checks."""

    _checks: tuple[BaseGenericCheck, ...]

    @property
    def config(self) -> dict:
        """An aggregate has no on_failure_policy of its own - its disposition is derived from its sub-checks' results."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "id": self.id,
            "version": self.version,
            "required_data": self.required_data,
            "failure_message": self.failure_message,
        }

    def _describe(self) -> dict:
        return {
            **super()._describe(),
            "checks": [c._describe() for c in self._checks],
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        """
        Run all sub-checks and return results.
        Short circuits if a check marked to short circuit (e.g. EmptyFieldCheck) fails.
        """

        results: list[Result] = []

        for check in self._checks:
            result = check.run(data_registry)
            results.append(result)

            if check._short_circuits_on_failure and not result.passed:
                break

        if self._passed(results):
            return self._result(passed=True, results=results)
        else:
            return self._result(passed=False, results=results, message=self.failure_message)

    def _passed(self, results: list[Result]) -> bool:
        """The aggregate passes only if every sub-check passed."""
        return all(r.passed for r in results)

    def _disposition(self, results: list[Result]) -> Disposition:  # type: ignore
        """The aggregate disposition is the most severe disposition among its sub-check results."""
        if any(r.disposition == Disposition.REJECT for r in results):
            return Disposition.REJECT
        if any(r.disposition == Disposition.WARN for r in results):
            return Disposition.WARN
        return Disposition.OK

    def _result(  # type: ignore
        self,
        passed: bool,
        results: list[Result],
        message: str = "",
    ) -> Result:
        return Result(
            check_config=self.config,
            passed=passed,
            disposition=self._disposition(results),
            message=message,
            results=results,
        )


class BaseMetadataAggregateCheck(BaseAggregateCheck):
    """An extension of BaseAggregateCheck for checks on a single metadata field."""

    field: str
    required_data = {"metadata"}

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "field": self.field,
        }

    @staticmethod
    def cleanup(value: str) -> str:
        return value

    @classmethod
    def check(cls, value: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(**{cls.field: value})))
