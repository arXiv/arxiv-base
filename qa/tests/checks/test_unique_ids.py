"""Consistency checks across every implemented check class, not just the registered ones."""

import qa.checks  # noqa: F401  imports every check module so all subclasses are defined
from qa.checks.base import BaseCheck


def _all_check_classes() -> list[type[BaseCheck]]:
    """Recursively collect every concrete check class (one that declares its own id/name)."""
    classes: list[type[BaseCheck]] = []
    seen: set[type[BaseCheck]] = set()
    stack = [BaseCheck]

    while stack:
        cls = stack.pop()
        for sub in cls.__subclasses__():
            if sub in seen:
                continue
            seen.add(sub)
            stack.append(sub)
            if "id" in vars(sub):
                classes.append(sub)

    return classes


class TestCheckIds:
    def test_all_check_ids_unique(self):
        classes = _all_check_classes()
        ids = [cls.id for cls in classes]
        assert sorted(ids) == sorted(set(ids))


class TestCheckNames:
    def test_all_check_names_unique(self):
        classes = _all_check_classes()
        names = [cls.name.lower() for cls in classes]
        assert sorted(names) == sorted(set(names))
