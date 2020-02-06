"""Tests version tag."""
from unittest import TestCase

from .tag_check import is_regressive_version


class TestVersions(TestCase):
    def good(self):
        self.assertFalse(is_regressive_version('0.0.1', []))
        self.assertFalse(is_regressive_version('1.1.1', ['1.0.0']))
        self.assertFalse(is_regressive_version('2.0.0', ['1.0.0']))
        self.assertFalse(is_regressive_version('1.0.0-build2', ['1.0.0-build1']))
        self.assertFalse(is_regressive_version('1.0.0-beta', ['1.0.0-alpha']))
        self.assertFalse(is_regressive_version('1.0.0', ['1.0.0-alpha']))

    def bad(self):
        self.assertTrue(is_regressive_version('0.1.1', ['1.0.0']))
        self.assertTrue(is_regressive_version('0.0.1', ['1.0.0']))
        self.assertTrue(is_regressive_version('1.0.0-alpha', ['1.0.0-beta']))
        self.assertTrue(is_regressive_version('1.0.0', ['1.0.0']))
        self.assertTrue(is_regressive_version('1.0.0-alpha', ['1.0.0']))
        self.assertTrue(is_regressive_version('1.1.0', ['1.2.0']))
        self.assertTrue(is_regressive_version('1.0.1', ['1.0.2']))

    def testx(self):
        self.assertFalse(is_regressive_version('1.2.0', ['1.1.0']))
        self.assertTrue(is_regressive_version('1.2.0', ['1.2.0']))
        self.assertTrue(is_regressive_version('1.2.0', ['1.3.0']))

        
