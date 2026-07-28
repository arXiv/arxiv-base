"""Tests for MetadataFieldsTotalLinesNotExceeded."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Metadata, OnFailurePolicy, QaDataRegistry
from qa.checks.metadata.field_line_totals import MetadataFieldsTotalLinesNotExceeded


class TestMetadataFieldsTotalLinesNotExceeded:
    def test_pass_normal(self):
        metadata = Metadata(title="A title", authors="Fred Smith", comments="12 pages")
        assert MetadataFieldsTotalLinesNotExceeded.check(metadata).passed

    def test_pass_all_fields_empty(self):
        assert MetadataFieldsTotalLinesNotExceeded.check(Metadata()).passed

    def test_pass_at_limit(self):
        metadata = Metadata(authors="\n".join(f"Author {i}" for i in range(25)))
        assert MetadataFieldsTotalLinesNotExceeded.check(metadata).passed

    def test_fail_over_limit(self):
        metadata = Metadata(authors="\n".join(f"Author {i}" for i in range(20)), title="line1\nline2\nline3\nline4\nline5\nline6")
        result = MetadataFieldsTotalLinesNotExceeded.check(metadata)
        assert not result.passed

    def test_fail_combined_across_fields(self):
        metadata = Metadata(
            title="line1\nline2\nline3\nline4",
            authors="line1\nline2\nline3\nline4",
            comments="line1\nline2\nline3\nline4",
            msc_class="line1\nline2\nline3\nline4",
            acm_class="line1\nline2\nline3\nline4",
            journal_ref="line1\nline2\nline3\nline4",
            doi="line1\nline2\nline3\nline4",
        )
        result = MetadataFieldsTotalLinesNotExceeded.check(metadata)
        assert not result.passed

    def test_abstract_not_counted(self):
        metadata = Metadata(abstract="\n".join(f"Line {i}" for i in range(50)))
        assert MetadataFieldsTotalLinesNotExceeded.check(metadata).passed

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            MetadataFieldsTotalLinesNotExceeded().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = MetadataFieldsTotalLinesNotExceeded.check(Metadata())
        assert result.check_config["name"] == "metadata_fields_total_lines_not_exceeded"
        assert result.check_config["id"] == 1000
        assert result.check_config["version"] == "1.0.0"
        assert result.check_config["on_failure_policy"] == OnFailurePolicy.REJECT
