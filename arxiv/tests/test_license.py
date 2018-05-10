"""Tests for arXiv taxonomy module."""
from unittest import TestCase
from arxiv.license import LICENSES, CURRENT_LICENSE_URIS


class TestLicense(TestCase):
    """Tests for the arXiv license definitions."""

    def test_current_license_uris(self):
        """Tests for the current active licenses."""
        self.assertListEqual(
            CURRENT_LICENSE_URIS,
            [
                'http://arxiv.org/licenses/nonexclusive-distrib/1.0/',
                'http://creativecommons.org/licenses/by/4.0/',
                'http://creativecommons.org/licenses/by-sa/4.0/',
                'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'http://creativecommons.org/publicdomain/zero/1.0/'
            ],
            'current license URIs match'
        )
