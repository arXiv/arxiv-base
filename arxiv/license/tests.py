"""Tests for arXiv taxonomy module."""
from unittest import TestCase
from .  import LICENSES, CURRENT_LICENSE_URIS, ASSUMED_LICENSE_URI


class TestLicense(TestCase):
    """Tests for the arXiv license definitions."""

    def test_current_license_uris(self):
        """Regression test for the current active licenses."""
        self.assertListEqual(
            CURRENT_LICENSE_URIS,
            [
                'http://creativecommons.org/licenses/by/4.0/',
                'http://creativecommons.org/licenses/by-sa/4.0/',
                'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'http://creativecommons.org/licenses/by-nc-nd/4.0/',
                'http://arxiv.org/licenses/nonexclusive-distrib/1.0/',
                'http://creativecommons.org/publicdomain/zero/1.0/'
            ],
            'current license URIs match'
        )

    def test_licenses_are_valid(self):
        """Test licenses contain required key/values."""
        for uri, license in LICENSES.items():
            self.assertIn('label', license)
            self.assertTrue(license['label'])
            self.assertIn('is_current', license)
            self.assertIsInstance(license['is_current'], bool)
            self.assertIn('order', license)
            self.assertIsInstance(license['order'], int)
            if 'icon_uri' in license:
                self.assertTrue(license['icon_uri'])
            if 'note' in license:
                self.assertTrue(license['note'])

    def test_assumed_license_is_valid(self):
        """Test assumed license is defined in licenses."""
        self.assertIn(ASSUMED_LICENSE_URI, LICENSES)
