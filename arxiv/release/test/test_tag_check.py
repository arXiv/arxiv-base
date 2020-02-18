"""Tests version tag."""
from unittest import TestCase

from arxiv.release.tag_check import is_valid_python_public_version


class TestVersions(TestCase):

    def test_python_version(self):
        self.assertTrue(is_valid_python_public_version('1.2.0'))
        self.assertTrue(is_valid_python_public_version('1.2'))
        self.assertTrue(is_valid_python_public_version('1.2.3'))
        self.assertTrue(is_valid_python_public_version('1.2.30'))
        self.assertTrue(is_valid_python_public_version('1.2.1rc2'))
        self.assertTrue(is_valid_python_public_version('1.2.1rc23'))

        self.assertTrue(is_valid_python_public_version('1.2.1.post2'))
        self.assertTrue(is_valid_python_public_version('1.2.1.dev234'))
        self.assertTrue(is_valid_python_public_version('1.2.post1'))
        self.assertTrue(is_valid_python_public_version('1.2.dev1'))

        self.assertTrue(is_valid_python_public_version('1.2.1b1'))
        self.assertTrue(is_valid_python_public_version('1.2.1a1'))
        self.assertTrue(is_valid_python_public_version('1.2b1'))
        self.assertTrue(is_valid_python_public_version('1.2a1'))

        self.assertTrue(is_valid_python_public_version('1.2.0-rc1'))
        self.assertFalse(is_valid_python_public_version('1.2.0ll2k-@#$'))
        self.assertFalse(is_valid_python_public_version('xx.2.0ll2k-@#$'))
        self.assertFalse(is_valid_python_public_version('1.2.0-rc1-pylocalstuff'))
