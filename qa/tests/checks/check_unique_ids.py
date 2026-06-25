"""Some consistency checks on all_checks."""

from qa.checks import checks as all_checks

class TestCheckIds:
    def test_all_check_ids_unique(self):
        assert len(all_checks) == len(set([check.id for check in all_checks]))

class TestCheckNames:
    def test_all_check_names_unique(self):
        assert len(all_checks) == len(set([check.name.lower() for check in all_checks]))

