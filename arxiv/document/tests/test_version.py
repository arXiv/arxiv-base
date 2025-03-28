from datetime import datetime

import pytest

from arxiv.document.version import VersionEntry, SourceFlag


def test_version():
    version_entry = VersionEntry(1,
                                 "something or other",
                                 datetime(2025, 3, 28, 10, 30, 0),
                                 1000,  # kb
                                 SourceFlag(''),
                                 False,
                                 'pdftex',
                                 True
                                 )
    assert version_entry.version == 1
    assert not version_entry.withdrawn_or_ignore
    assert set(version_entry.formats()) == set(['src', 'pdf', 'other'])
