r"""
Patterns and functions to detect arXiv ids and Urls in text.

Functions to detect arXiv ids, URLs and DOI in text.
Functions to transform them to <a> tags.

These were originally jinja filters but became a little too big
for that so they were split out and made more general so they didn't
rely on the Flask context.

There are several classes of patterns we want to match but there is
some overlap in these patterns. To avoid looking for and parsing HTML in each
jinja filter, detecting these patterns is combined.

So far we are looking for:
DOIs            DOI: 10.1145/0001234.1234567
arXiv IDS:      1234.12345 1234.12345v1 hep-ph1307.1843
HTTP URLs:      http://something.org/myPaper/1234.12345
FTP URLs:       ftp://example.com/files/1234.12345

Just matching for arXiv ids with \d{4}\.\d{4,5} will match several of
these. To deal with this we are priortizing the matches and
interupting once one is found.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv matches.

Updated 18 January, 2019: refactored to combine arXiv + DOI regexes with URL
matching and link generation provided by `bleach
<https://bleach.readthedocs.io>`_. The bleach URL regex is extended a bit to
handle FTP addresses.
"""
from typing import Optional, List, Pattern, Match, Tuple, Callable, \
    NamedTuple, Dict, Union, Mapping
import re
from functools import partial
from urllib.parse import quote, urlparse

from flask import url_for
from jinja2 import Markup, escape
import bleach

from arxiv import identifier
from . import clickthrough


Attrs = Dict[Union[str, Tuple[None, str]], str]
Callback = Callable[[Attrs, bool], Attrs]


def _without_group_names(pattern: Pattern) -> str:
    ptn: str = re.sub(r'\(\?P<[^>\!]+>', '(?:', pattern.pattern)
    return ptn


DOI = re.compile(   # '10.1145/0001234.1234567'
    r'(?P<doi>10.\d{4,9}/[-._;()/:A-Z0-9]+)',
    re.I
)
"""
Pattern for matching DOIs.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv matches.

Only using the most general express from
https://www.crossref.org/blog/dois-and-matching-regular-expressions/
"""

ARXIV_PATTERNS = [
    identifier.OLD_STYLE_WITH_ARCHIVE,  # math/0501233 hep-ph/0611734
    identifier.OLD_STYLE_WITH_CATEGORY,  # math.GR/0601136v3 math.GR/0601136
    identifier.STANDARD  # 1609.05068 1207.1234v1 1207.1234 1807.12345v12
]
ARXIV_ID = re.compile(
    "|".join([rf"(?:{_without_group_names(pattern)})"
              for pattern in ARXIV_PATTERNS]),
    re.IGNORECASE | re.VERBOSE | re.UNICODE
)

OKCHARS = r'([a-z0-9,_.\-+~:]|%[a-f0-9]*)'
"""Chacters that are acceptable during PATH, QUERY and ANCHOR parts"""

PATH = rf'(?P<PATH>(/{OKCHARS}*)+)?'
"""Regex for path part of URLs for use in urlize"""

FTP = re.compile(rf'(?P<url>(?:ftp://)({OKCHARS}|(@))*{PATH})', re.I)
"""Regex to match FTP URLs in text."""

IP_ADDRESS = (r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
              r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')
"""Regex to match an IP address."""

TLDS = '|'.join(bleach.linkifier.TLDS)
PROTOCOLS = '|'.join(bleach.linkifier.html5lib_shim.allowed_protocols)
URL = re.compile(
    rf"""(?:{FTP.pattern})|
    (?:\(*  # Match any opening parentheses.
    \b(?<![@/])(?:(?:{PROTOCOLS}):/{{0,3}}(?:(?:\w+:)?\w+@)?)?  # http://
    (?:
        (?:([\w-]+\.)+(?:{TLDS}))   # Conventional URL
        |(?:{IP_ADDRESS})           # IP address
    )(?:\:[0-9]+)?(?!\.\w)\b        # Port
    (?:[/?][^\s\{{\}}\|\\\^\[\]`<>"]*)?)
        # /path/zz (excluding "unsafe" chars from RFC 1738,
        # except for # and ~, which happen in practice)
    """,
    re.IGNORECASE | re.VERBOSE | re.UNICODE
)


def arxiv_id_to_url(arxiv_id: str) -> str:
    """Generate an URL for an arXiv ID."""
    url: str = url_for('abs_by_id', paper_id=arxiv_id)
    return url


def url_for_doi(doi: str) -> str:
    """Generate an URL for a DOI."""
    quoted_doi = quote(doi, safe='/')
    return f'https://dx.doi.org/{quoted_doi}'


def clickthrough_url_for_doi(doi: str) -> str:
    """Generate a clickthrough URL for a DOI."""
    return clickthrough.clickthrough_url(url_for_doi(doi))


def _extend_class_attr(attrs: Attrs, new_class: str) -> Attrs:
    if (None, 'class') not in attrs:
        attrs[(None, 'class')] = ''
    attrs[(None, 'class')] = (attrs[(None, 'class')] + f' {new_class}').strip()
    return attrs


def _add_rel_external(attrs: Attrs, new: bool = False) -> Attrs:
    o = urlparse(attrs[(None, 'href')])
    if not o.netloc.split(':')[0].endswith('arxiv.org'):   # External link?
        attrs[(None, 'rel')] = 'external'
        attrs['_text'] = f'this {o.scheme} URL'    # Replaces the link text.
        _extend_class_attr(attrs, 'link-external')
    elif (None, 'data-arxiv-id') not in attrs \
            and (None, 'data-doi') not in attrs:
        attrs['_text'] = f'this {o.scheme} URL'    # Replaces the link text.
        _extend_class_attr(attrs, 'link-internal')
    return attrs


def _add_scheme_info(attrs: Attrs, new: bool = False) -> Attrs:
    o = urlparse(attrs[(None, 'href')])
    if (None, 'class') not in attrs:
        attrs[(None, 'class')] = ''
    _extend_class_attr(attrs, f'link-{o.scheme}')
    return attrs


def _handle_arxiv_url(attrs: Attrs, new: bool = False) -> Attrs:
    """
    Screen for reference to an arXiv e-print, and generate URL.

    If the :ref:`.ARXIV_ID` pattern is used, it will generate a link with the
    identifier as a the target. We need to intercept these links, and generate
    a real URL.
    """
    href = attrs[(None, 'href')]
    if '://' in href:   # http://1902.00123
        target = href.split('://', 1)[1]
        prefix = ''
    elif ':' in href:   # arxiv:1902.00123
        target = href.split(':', 1)[1]
        prefix = 'arXiv:'
    else:
        target = href
        prefix = ''
    if ARXIV_ID.match(target):
        attrs[(None, 'href')] = arxiv_id_to_url(target)
        attrs['_text'] = f'{prefix}{target}'
        attrs[(None, 'data-arxiv-id')] = target     # Add arxiv="<arxiv id>"
    return attrs


def _handle_doi_url(attrs: Attrs, new: bool = False) -> Attrs:
    """
    Screen for reference to a DOI, and generate a URL.

    If the :ref:`.DOI` pattern is used, it will generate a link with the
    doi as a the target. We need to intercept these links, and generate
    a real URL.
    """
    href = attrs[(None, 'href')]
    if '://' in href:
        target = href.split('://', 1)[1]
        prefix = ''
    elif ':' in href:
        target = href.split(':', 1)[1]
        prefix = 'doi:'
    else:
        target = href
        prefix = ''
    if DOI.match(target):
        attrs[(None, 'href')] = clickthrough_url_for_doi(target)
        attrs['_text'] = f'{prefix}{target}'
        attrs[(None, 'data-doi')] = target     # Add arxiv="<arxiv id>"
    return attrs


PATTERNS = {
    'doi': DOI,
    'url': URL,
    'arxiv_id': ARXIV_ID
}
ORDER = ['arxiv_id', 'doi', 'url']
SUPPORTED_KINDS = ORDER
"""Identifier types that we can currently match and convert to to URLs."""

DEFAULT_CALLBACKS: List[Callback] = [
    _handle_doi_url,
    _handle_arxiv_url,
    _add_rel_external,
    _add_scheme_info
]


def _get_pattern(kinds: List[str]) -> Pattern:
    return re.compile(
        '|'.join([rf'(?:{PATTERNS[kind].pattern})' for kind
                 in sorted(kinds, key=lambda kind: ORDER.index(kind))]),
        re.IGNORECASE | re.VERBOSE | re.UNICODE
    )


def _get_linker(kinds: List[str],
                callbacks: List[Callback] = DEFAULT_CALLBACKS) \
        -> Callable[[str], str]:
    linker: Callable[[str], str] = bleach.linkifier.Linker(
        callbacks=callbacks,
        skip_tags=['a'],
        url_re=_get_pattern(kinds)
    ).linkify
    return linker


def urlize(text: str, kinds: List[str] = SUPPORTED_KINDS) -> str:
    """
    Convert URLs and certain identifiers to HTML links.

    Parameters
    ----------
    text : str
        Some text containing identifiers and/or URLs.
    kinds : list
        Names (from :ref:`SUPPORTED_KINDS`) of identifiers to match.

    Returns
    -------
    str
        The passed text, with identifiers and/or URLs converted to HTML links.

    """
    return _get_linker(kinds)(text)


def urlizer(kinds: List[str] = SUPPORTED_KINDS) -> Callable[[str], str]:
    """
    Generate a function to convert tokens to links.

    Parameters
    ----------
    kinds : list
        Names (from :ref:`SUPPORTED_KINDS`) of identifiers to match and
        convert.

    Returns
    -------
    callable
        A function with signature ``(str) -> str`` that converts identifiers
        to HTML links.

    """
    return _get_linker(kinds)
