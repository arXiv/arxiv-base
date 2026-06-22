# qa

Quality assurance checks for arXiv papers.

A `checks` object of type `list[BaseCheck]` is initialized when the package is imported. It serves as the 'registry' of all exposed checks. 

See the `qa-checks` API for a registry endpoint that can be called to return documentation on all implemented checks.

```
qa/
├── checks/
│   ├── base.py          # Abstract base classes for all check types
│   ├── models.py        # Data models (e.g. Result, Disposition)
│   ├── generic/         # Reusable checks (e.g. text checks, author name checks)
│   └── metadata/        # Field-level aggregate checks (i.e. TitleIsValid)
└── reports/
    └── models/          # Data models for data processing reports (e.g. FulltextReport)
```

- [How to run a check](#how-to-run-a-check)
- [Developing in `qa`](#developing-in-qa)
  - [Adding a new basic check](#adding-a-new-basic-check)
  - [Adding a new generic check](#adding-a-new-generic-check)
  - [Adding a new aggregate check](#adding-a-new-aggregate-check)
  - [Updating a check](#updating-a-check)

## How to run a check

Use the convenience class method:

```python
from qa.checks.metadata.title import TitleIsValid

result = TitleIsValid.check("A Valid Paper Title")
result.passed        # True/False
result.disposition   # Disposition.OK | Disposition.WARN | Disposition.REJECT
result.results       # list of sub-check Results
```

Each failing check result includes `offsets` — character-level spans identifying exactly where in the field the problem occurs.

## Developing in `qa`

See `Makefile` for lifecycle commands.

### Updating a check

Whenever making changes to the logic or configuration of a check (including the `on_failure_policy`), be sure to bump that check's `version`.

### Adding a new basic check

A basic check directly extends `BaseCheck`. Use this when the check is specific to one input (i.e. fulltext) and not intended to be reused elsewhere.

```python
class FulltextDoesNotContainFoo(BaseCheck):
    name = "fulltext_does_not_contain_foo"
    id = 99          # next available id
    version = "1.0.0"
    description = "The fulltext of the paper does not contain 'foo'."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Fulltext contains 'foo'."

    required_inputs = {"fulltext"}

    def _run(self, inputs: Inputs) -> Result:
        passed = "foo" not in inputs.fulltext
        return self._result(passed=passed, message="" if passed else self.failure_message)
```

Expose the check by registering an instance in `checks` at `qa/checks/__init__.py`.

### Adding a new generic check
A generic check is a check that can be reused across multiple fields with different configuration. It is called by an aggregate check.

Add a class extending `BaseGenericPatternCheck` or `BaseGenericCheck`.

For regex-based checks, extend `BaseGenericPatternCheck` — matches are treated as failures:

```python
class DoesNotContainFoo(BaseGenericPatternCheck):
    name = "does_not_contain_foo"
    id = 99          # next available id
    version = "1.0.0"
    description = "The value does not contain 'foo'."
    failure_message = "Contains 'foo'."
    _pattern = r"foo"
```

For checks with custom logic, extend `BaseGenericCheck` and implement `_run`:

```python
class PassesCustomLogic(BaseGenericCheck):
    name = "passes_custom_logic"
    id = 99
    version = "1.0.0"
    description = "..."
    failure_message = "..."

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)
        passed = ...  # your logic here
        return self._result(passed=passed, message="" if passed else self.failure_message)
```

### Adding a new aggregate check

Add a class extending `BaseAggregateCheck`.

Populate `_checks` with the generic checks to run, and define a `check()` classmethod for triggering it.


```python
class FooIsValid(BaseAggregateCheck):
    """Aggregate check for the metadata foo field."""

    name = "foo_is_valid"
    id = 600         # next available id
    version = "1.0.0"
    description = "The metadata foo field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Foo is invalid."

    required_inputs = {"metadata"}

    @classmethod
    def check(cls, foo: str | None) -> Result:
        return cls().run(Inputs(metadata=Metadata(foo=foo)))

    _checks = (
        NotTooLong(2000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="foo"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="foo"),
    )
```

Expose the check by registering an instance in `checks` at `qa/checks/__init__.py`.
