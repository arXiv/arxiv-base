"""Contract for the metadata_checks list.

Callers run these checks on posted metadata alone and key each result by the
check's field (e.g. modapi's metadata-validation route), so every check here
must be about one metadata field and need nothing but metadata.
"""

from qa.checks import metadata_checks
from qa.checks.base import BaseMetadataAggregateCheck
from qa.checks.models import Metadata, QaDataRegistry


class TestMetadataChecks:
    def test_all_are_single_field_metadata_checks(self):
        for check in metadata_checks:
            assert isinstance(check, BaseMetadataAggregateCheck), check.name

    def test_fields_are_metadata_fields(self):
        for check in metadata_checks:
            assert check.field in Metadata.model_fields, check.name

    def test_fields_are_unique(self):
        fields = [check.field for check in metadata_checks]
        assert sorted(fields) == sorted(set(fields))

    def test_only_require_metadata(self):
        for check in metadata_checks:
            assert check.required_data == {"metadata"}, check.name

    def test_run_with_metadata_alone(self):
        registry = QaDataRegistry(metadata=Metadata(title="A title", authors="A. Tester"))
        for check in metadata_checks:
            check.run(registry)
