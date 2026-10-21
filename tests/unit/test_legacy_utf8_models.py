"""Checks the Legacy* ("twice cooked" utf8) columns across all of arxiv.db.models. No database needed.
"""
import arxiv.db.models  # noqa: F401   (register models)
from arxiv.db import metadata
from arxiv.db.legacy_utf8_table import check_legacy_utf8_tables

def test_legacy_columns_are_only_in_utf8_tables() -> None:
    """Applying the double encoding to a latin1 (or undeclared) table would corrupt its data."""
    assert check_legacy_utf8_tables(metadata) == []
