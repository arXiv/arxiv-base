"""Utility functions for arxiv.search."""
# pylint: disable=C0330

import re
from arxiv import taxonomy

__all__ = ('parse_arxiv_id', )

_archive = '|'.join([re.escape(key) for key in taxonomy.ARCHIVES.keys()])
"""string for use in Regex for all arXiv archives"""

_category = '|'.join([re.escape(key) for key in taxonomy.CATEGORIES.keys()])

_prefix = r'(?P<arxiv_prefix>ar[xX]iv:)'
"""
Attempt to catch the arxiv prefix in front of arxiv ids.

E.g. so that it can be included in the <a> tag anchor (ARXIVNG-1284).
"""

ARXIV_REGEX = (
    "^(ar[xX]iv:)?((?:(?:(?:%s)(?:[.][A-Z]{2})?/[0-9]{2}(?:0[1-9]|1[0-2])"
    "\\d{3}(?:[vV]\\d+)?))|(?:(?:[0-9]{2}(?:0[1-9]|1[0-2])[.]"
    "\\d{4,5}(?:[vV]\\d+)?)))$" % _category
)

OLD_STYLE_WITH_ARCHIVE = re.compile(
    r'(?:%s)?(?P<arxiv_id>(%s)\/\d{2}[01]\d{4}(v\d*)?)' % (_prefix, _archive),
    re.I
)

OLD_STYLE_WITH_CATEGORY = re.compile(
    r'(?:%s)?(?P<arxiv_id>(%s)\/\d{2}[01]\d{4}(v\d*)?)' % (_prefix, _category),
    re.I
)

OLD_STYLE = re.compile(
    r'(?:%s)?(?P<arxiv_id>(%s)\/\d{2}[01]\d{4}(v\d*)?)'
    % (_prefix, f'{_archive}|{_category}'),
    re.I
)

STANDARD = re.compile(
    r'(?<![\d=\.])(?:%s)?(?P<arxiv_id>\d{4}\.\d{4,5}(v\d*)?)'
    % _prefix,
    re.I
)


def parse_arxiv_id(value: str) -> str:
    """
    Parse arxiv id from string.

    Raises `ValidationError` if no arXiv ID.
    """
    m = re.search(STANDARD, value)
    if m:
        return m.group('arxiv_id')
    m = re.search(OLD_STYLE, value)
    if m:
        return m.group('arxiv_id')
    raise ValueError('Not a valid arXiv ID')
