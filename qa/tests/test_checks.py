"""Unit tests for QA report models."""

from unittest import TestCase

from arxiv.metadata import (
    FieldName,
    Complaint,
)

from qa_models.checks import (
    Check,
    check_to_check_id,
    fieldname_to_check,
    metadata_check_to_check_id,
    flagged_term_to_check_id,
)


class TestChecks(TestCase):
    def test_checks(self):
        self.assertEqual( Check.OVERSIZE_FILES.value, 48 )
        self.assertNotEqual( Check.OVERSIZE_FILES, Check.PDFPAGES )
        self.assertNotEqual( Check.OVERSIZE_FILES, Check.OVERSIZE_IMAGES )

    def test_check_to_check_id(self):
        self.assertEqual( check_to_check_id(Check.OVERSIZE_FILES), 48 )

    def test_fieldname_to_check(self):
        self.assertEqual(
            fieldname_to_check(FieldName.AUTHORS),
            Check.METADATA_AUTHORS
        )

    def test_metadata_check_to_check_id(self):
        self.assertEqual(
            metadata_check_to_check_id(FieldName.AUTHORS, Complaint.INVALID_DOI),
            250
        )

    def test_flagged_term_to_check_id(self):
        self.assertEqual(
            flagged_term_to_check_id( 55 ),
            1055
        )
        
