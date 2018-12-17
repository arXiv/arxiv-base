"""Fuzz test for :mod:`arxiv.base.urls.clickthrough`."""

import unittest

from hypothesis import given
from hypothesis.strategies import text

from ..clickthrough import create_hash, is_hash_valid


class TestClickthroughFuzzTest(unittest.TestCase):
    """Fuzz tests for :func:`.create_hash` and :func:`.is_hash_valid`."""

    @given(text(), text())
    def test_clickthrough(self, s, v):
        """Generate a hash for a bunch of "urls" and a bunch of hashes."""
        h = create_hash(s, v)
        self.assertTrue(is_hash_valid(s, v, h))
