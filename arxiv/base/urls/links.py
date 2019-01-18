r"""
Patterns and functions to detect arXiv ids and Urls in text.

Functions to detech arXiv ids, URLs and DOI in text.
Functions to transform them to <a> tags.

These were originally jinja filters but became a little too big
for that so they were split out and made more general so they didn't
rely on the Flask context.

These all use expect input of Markup or non-markup text and return
Markup objects. This is because the <a> that get added need to avoid
double escaping.

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


class Matchable(NamedTuple):
    """Class for paterns."""

    examples: List[str]
    pattern: Pattern


Izer = Callable[[str], str]
Substituter = Callable[[Match, Izer],
                       Tuple[Union[Markup, str], Union[Markup, str]]]
URLType = Tuple[List[Matchable], Substituter, Izer]


def _identity(x: str) -> str:
    """Identity funciton for default in some places."""
    return x


DOI = re.compile(r'(?P<doi>10.\d{4,9}/[-._;()/:A-Z0-9]+)', re.I)
doi_patterns = [
    Matchable(['10.1145/0001234.1234567'], DOI)
]
"""
List of Matchable for DOIs in text.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv matches.

Only using the most general express from
https://www.crossref.org/blog/dois-and-matching-regular-expressions/
"""

basic_arxiv_id_patterns = [
    Matchable(['math/0501233', 'hep-ph/0611734', 'gr-qc/0112123'],
              identifier.OLD_STYLE_WITH_ARCHIVE),
    Matchable(['math.GR/0601136v3', 'math.GR/0601136'],
              identifier.OLD_STYLE_WITH_CATEGORY),
    Matchable(['1609.05068', '1207.1234v1', '1207.1234', '1807.12345',
               '1807.12345v1', '1807.12345v12'],
              identifier.STANDARD)
]
ARXIV_ID = re.compile(
    rf"""(?:{identifier.OLD_STYLE_WITH_ARCHIVE.pattern})
            | (?:{identifier.OLD_STYLE_WITH_CATEGORY.pattern})
            | (?:{identifier.STANDARD.pattern})""",
    re.IGNORECASE | re.VERBOSE | re.UNICODE
)

OKCHARS = r'([a-z0-9,_.\-+~:]|%[a-f0-9]*)'
"""Chacters that are acceptable during PATH, QUERY and ANCHOR parts"""

HOST_NAME = r'(?:[a-z0-9][a-z0-9\-.:]+[a-z0-9])'
"""Regex used to match host names in arXiv urlize.

This is not a perfect regex for a host name, It accepts only a sub-set
of hostnames to meet the needs of arxiv.

HOST_NAME must end with a simplified character to avoid capturing a
period.
"""

PATH = rf'(?P<PATH>(/{OKCHARS}*)+)?'
"""Regex for path part of URLs for use in urlize"""

QUERY = rf'(?P<QUERY>\?(&?({OKCHARS}*(={OKCHARS}*)?))*)?'
"""Regex for query part of URLs for use in urlize"""

ANCHOR = rf'(?P<ANCHOR>#({OKCHARS}|/)*)?'
"""Regex for anchor part of URLs for use in urlize"""

URLINTEXT_PAT = re.compile(r'(?P<url>(?:https?://)'
                           f'{HOST_NAME}{PATH}{QUERY}{ANCHOR})',
                           re.I)
"""Regex to match URLs in text."""

FTP = re.compile(rf'(?P<url>(?:ftp://)({OKCHARS}|(@))*{PATH})', re.I)
"""Regex to match FTP URLs in text."""

basic_url_patterns = [
    Matchable(['http://something.com/bla'], URLINTEXT_PAT),
    Matchable(['ftp://something.com/bla'], FTP)
]
"""List of Matchable to use when finding URLs in text"""

bad_arxiv_id_patterns = [
    re.compile('vixra', re.I),  # don't need to link to vixra
]
"""List of Regex patterns that will cause matching to be skipped for
the token."""

dois_ids_and_urls = basic_url_patterns + doi_patterns + basic_arxiv_id_patterns
"""
List of Matchable to use when finding DOIs, arXiv IDs, and URLs.

URLs are first because some URLs contain DOIs or arXiv IDS.

DOI are before arXiv ids because many DOIs are falsely matched by the
arxiv_id patterns.
"""


_bad_endings = ['.', ',', ':', ';', '&', '(', '[', '{']
"""These should not appear at the end of URLs because they are likely
part of the surrounding text"""


def _find_match(patterns: List[Matchable], token: str) \
        -> Optional[Tuple[Match, Matchable]]:
    """Find first in patterns that is found in txt."""
    for chgMtch in patterns:
        if chgMtch.pattern.flags:
            fnd = re.search(chgMtch.pattern, token)
        else:
            fnd = re.search(chgMtch.pattern, token, re.I)
        if fnd is not None:
            return (fnd, chgMtch)
    return None


def _transform_token(targets: Tuple[str, List[str], Substituter, Izer],
                     bad_patterns: List[Pattern], token: str) -> str:
    """
    Transform a token from text to one of the Matchables.

    This only transforms against the first of Matchable matched.
    Matching on this token will be skipped if any of the bad_patterns
    match the token (that is re.search).
    """
    for pattern in bad_patterns:
        if re.search(pattern, token):
            return token

    patterns = [p for _, ptns, _, _ in targets for p in ptns]    # type: ignore
    mtch = _find_match(patterns, token)
    if mtch is None:
        return token

    (match, _) = mtch
    keys = match.groupdict().keys()
    target_match = False
    for target_type, _, substituter, izer in targets:   # type: ignore
        if target_type in keys:
            (front, back) = substituter(match, izer)
            target_match = True
            break
    # If no substituters apply, there is nothing more to do.
    if not target_match:    # But this would be an odd case...
        return token

    if back:
        t_back = _transform_token(targets, bad_patterns, back)
        return front + Markup(t_back)   # type: ignore
    else:
        return front       # type: ignore


def id_substituter(match: Match, id_to_url: Izer) -> Tuple[Markup, str]:
    """Return match.string transformed for a arxiv id match."""
    aid = match.group('arxiv_id')
    prefix = 'arXiv:' if match.group('arxiv_prefix') else ''

    if aid[-1] in _bad_endings:
        arxiv_url = id_to_url(aid)[:-1]
        anchor = aid[:-1]
        back = aid[-1] + match.string[match.end():]
    else:
        arxiv_url = id_to_url(aid)
        anchor = prefix + aid
        back = match.string[match.end():]

    front = match.string[0:match.start()]
    return (Markup(f'{front}<a href="{arxiv_url}">{anchor}</a>'), back)


def doi_substituter(match: Match, url_for_doi: Izer) -> Tuple[Markup, str]:
    """Return match.string transformed for a DOI match."""
    doi = match.group('doi')
    if(doi[-1] in _bad_endings):
        back = match.string[match.end():] + doi[-1]
        doi = doi[:-1]
    else:
        back = match.string[match.end():]

    doi_url = url_for_doi(doi)

    anchor = escape(doi)
    front = match.string[0:match.start()]
    return (Markup(f'{front}<a href="{doi_url}">{anchor}</a>'), back)


_word_split_re = re.compile(r'(\s+)')
"""Regex to split to tokens during _to_tags.

Capturing group causes the splitting spaces to be included
in the returned list.
"""


def _to_tags(targets: Tuple[str, List[str], Substituter, Izer],
             bad_patterns: List[Pattern], text: str)-> str:
    """Split text to tokens, do _transform_token for each, return results."""
    transform_token = partial(_transform_token, targets, bad_patterns)

    if not hasattr(text, '__html__'):
        text = Markup(escape(text))

    words = _word_split_re.split(text)
    for i, token in enumerate(words):
        token_2 = transform_token(token)
        if token_2 != token:
            words[i] = token_2
    result = u''.join(words)
    return Markup(result)


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


def extend_class_attr(attrs: Mapping, new_class: str) -> Mapping:
    if (None, 'class') not in attrs:
        attrs[(None, 'class')] = ''
    attrs[(None, 'class')] = (attrs[(None, 'class')] + f' {new_class}').strip()


def add_rel_external(attrs: Mapping, new: bool = False) -> Mapping:
    o = urlparse(attrs[(None, 'href')])
    if not o.netloc.split(':')[0].endswith('arxiv.org'):   # External link?
        attrs[(None, 'rel')] = 'external'
        attrs['_text'] = f'this {o.scheme} URL'    # Replaces the link text.
        extend_class_attr(attrs, 'link-external')
    elif (None, 'arxiv') not in attrs and (None, 'doi') not in attrs:
        attrs['_text'] = f'this {o.scheme} URL'    # Replaces the link text.
        extend_class_attr(attrs, 'link-internal')
    return attrs


def add_scheme_info(attrs: Mapping, new: bool = False) -> Mapping:
    o = urlparse(attrs[(None, 'href')])
    if (None, 'class') not in attrs:
        attrs[(None, 'class')] = ''
    extend_class_attr(attrs, f'link-{o.scheme}')
    return attrs


def handle_arxiv_url(attrs: Mapping, new: bool = False) -> Mapping:
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
        attrs[(None, 'arxiv')] = target     # Add arxiv="<arxiv id>"
    return attrs


def handle_doi_url(attrs: Mapping, new: bool = False) -> Mapping:
    """
    Screen for reference to an DOIs, and generate URL.

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
    print(target, DOI.match(target), DOI.search(target))
    if DOI.match(target):
        attrs[(None, 'href')] = clickthrough_url_for_doi(target)
        attrs['_text'] = f'{prefix}{target}'
        attrs[(None, 'doi')] = target     # Add arxiv="<arxiv id>"
    return attrs



REGEX_URL_KINDS: Dict[str, URLType] = {
    # 'url': (basic_url_patterns, url_substituter, _identity),
    'arxiv_id': (basic_arxiv_id_patterns, id_substituter, arxiv_id_to_url),
    'doi': (doi_patterns, doi_substituter, clickthrough_url_for_doi),
}

IP_ADDRESS = r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'


# TODO: incorporate DOI into this regex, optionally; use callbacks to detect
# things that need clickthrough URLs. Consider even doing arXiv IDs this way.
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

PATTERNS = {
    'doi': DOI,
    'url': URL,
    'arxiv_id': ARXIV_ID
}
ORDER = ['arxiv_id', 'doi', 'url']
SUPPORTED_KINDS = ORDER


def _get_pattern(kinds: List[str]) -> Pattern:
    return re.compile(
        '|'.join([rf'(?:{PATTERNS[kind].pattern})' for kind
                 in sorted(kinds, key=lambda kind: ORDER.index(kind))]),
        re.IGNORECASE | re.VERBOSE | re.UNICODE
    )


def _get_linker(kinds: List[str]) -> Callable[[str], str]:
    return bleach.linkifier.Linker(
        callbacks=[handle_doi_url, handle_arxiv_url, add_rel_external, add_scheme_info],
        skip_tags=['a'],
        url_re=_get_pattern(kinds)
    ).linkify


def urlize(text: str, kinds: List[str] = SUPPORTED_KINDS) -> str:
    """Convert URLs and certain identifiers to links."""
    return _get_linker(kinds)(text)


def urlizer(kinds: List[str] = SUPPORTED_KINDS):
    return _get_linker(kinds)
