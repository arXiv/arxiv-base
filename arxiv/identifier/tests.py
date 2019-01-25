"""Tests for :mod:`arxiv.identifier`."""

from unittest import TestCase

from . import parse_arxiv_id


class TestParseArXivID(TestCase):
    """Tests for :func:`parse_arxiv_id`."""

    def test_old_style_with_archive(self):
        """Parse old-style arXiv IDs with archive names."""
        self.assertIsNotNone(parse_arxiv_id('math/9901123'))
        self.assertIsNotNone(parse_arxiv_id('hep-ex/9901123'))
        self.assertIsNotNone(parse_arxiv_id('gr-qc/9901123'))

    def test_old_style_with_category(self):
        """Parse old-style arXiv IDs with category names."""
        self.assertIsNotNone(parse_arxiv_id('math.NA/9901123'))
        self.assertIsNotNone(parse_arxiv_id('cs.DB/9901123'))

    def test_old_style_with_version(self):
        """Parse old-style arXiv IDs with version numbers."""
        self.assertIsNotNone(parse_arxiv_id('gr-qc/9901123v3'))

    def test_odd_mashup(self):
        """Parse identifer that combines old- and new-style."""
        self.assertIsNotNone(parse_arxiv_id('hep-ph/1203.12345v12'))

    def test_new_style(self):
        """Parse new-style identifiers."""
        self.assertIsNotNone(parse_arxiv_id('1202.1234'))
        self.assertIsNotNone(parse_arxiv_id('1203.12345'))

    def test_new_style_with_version(self):
        """Parse new-style with version numbers."""
        self.assertIsNotNone(parse_arxiv_id('1202.1234v1'))
        self.assertIsNotNone(parse_arxiv_id('1203.12345v1'))
        self.assertIsNotNone(parse_arxiv_id('1203.12345v12'))

    # slightly odd but seen in comments
