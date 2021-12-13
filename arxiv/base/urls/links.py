r"""
Patterns and functions to detect arXiv ids and URLs in text.

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
these. To deal with this we are prioritizing the matches and
interrupting once one is found.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv matches.

Updated 18 January, 2019: refactored to combine arXiv + DOI regexes with URL
matching and link generation provided by `bleach
<https://bleach.readthedocs.io>`_. The bleach URL regex is extended a bit to
handle FTP addresses.

Updated 20 March, 2019: refactored to provide independent bleach attribute
callbacks for each kind of link.
"""
from typing import (
    List,
    Pattern,
    Tuple,
    Callable,
    Dict,
    Union,
    Text,
    Any,
    MutableMapping,
)
import re
from functools import reduce
from urllib.parse import quote, urlparse

from flask import url_for, g
import bleach

from arxiv.taxonomy import CATEGORIES
from arxiv import identifier
from . import clickthrough


Attrs = MutableMapping[Any, Text]
Callback = Callable[[Attrs, bool], Attrs]
Callable_Linker = Callable[[str], str]


def _without_group_names(pattern: Pattern) -> str:
    ptn: str = re.sub(r"\(\?P<[^>\!]+>", "(?:", pattern.pattern)
    return ptn


DOI = re.compile(  # '10.1145/0001234.1234567'
    r"(?P<doi>10.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I
)
"""
Pattern for matching DOIs.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv id matches.

Only using the most general expression from
https://www.crossref.org/blog/dois-and-matching-regular-expressions/
"""


BROAD_DOI = re.compile(r"(?P<doi>\d{2,3}.\d{4,5}\/\S+)", re.I)
"""
Very broad pattern for matching DOIs in the abs DOI field.

Ex. 10.1175/1520-0469(1996)053<0946:ASTFHH>2.0.CO;2
Ex. 21.11130/00-1735-0000-0005-146A-E
"""

ARXIV_PATTERNS = [
    identifier.OLD_STYLE_WITH_ARCHIVE,  # math/0501233 hep-ph/0611734
    identifier.OLD_STYLE_WITH_CATEGORY,  # math.GR/0601136v3 math.GR/0601136
    identifier.STANDARD,  # 1609.05068 1207.1234v1 1207.1234 1807.12345v12
]
ARXIV_ID = re.compile(
    "|".join([rf"(?:{_without_group_names(pattern)})" for pattern in ARXIV_PATTERNS]),
    re.IGNORECASE | re.VERBOSE | re.UNICODE,
)

OKCHARS = r"([a-z0-9,_.\-+~:]|%[a-f0-9]*)"
"""Characters that are acceptable during PATH, QUERY and ANCHOR parts"""

PATH = rf"(?P<PATH>(/{OKCHARS}*)+)?"
"""Regex for path part of URLs for use in urlize"""

FTP = re.compile(rf"(?P<url>(?:ftp://)({OKCHARS}|(@))*{PATH})", re.I)
"""Regex to match FTP URLs in text."""

IP_ADDRESS = (
    r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
)
"""Regex to match an IP address."""

TLDS = "|".join(bleach.linkifier.TLDS)
PROTOCOLS = "|".join(bleach.linkifier.html5lib_shim.allowed_protocols)
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
    re.IGNORECASE | re.VERBOSE | re.UNICODE,
)


def arxiv_id_to_url(arxiv_id: str) -> str:
    """Generate an URL for an arXiv ID."""
    url: str = url_for("abs_by_id", paper_id=arxiv_id)
    return url


def url_for_doi(doi: str) -> str:
    """Generate an URL for a DOI."""
    quoted_doi = quote(doi, safe="/")
    return f"https://doi.org/{quoted_doi}"


def clickthrough_url_for_doi(doi: str) -> str:
    """Generate a clickthrough URL for a DOI."""
    return clickthrough.clickthrough_url(url_for_doi(doi))


def _extend_class_attr(attrs: Attrs, new_class: str) -> Attrs:
    if (None, "class") not in attrs:
        attrs[(None, "class")] = ""
    attrs[(None, "class")] = (attrs[(None, "class")] + f" {new_class}").strip()
    return attrs


def _add_rel(attrs: Attrs, new: bool = False) -> Attrs:
    """Check if href is internal or external and adds attrs as appropriate."""
    o = urlparse(attrs[(None, "href")])
    if not o.netloc.split(":")[0].endswith("arxiv.org"):  # External link?
        return _add_rel_external(attrs, new)
    else:
        return _add_rel_internal(attrs, new)


def _add_rel_external(attrs: Attrs, new: bool = False) -> Attrs:
    """Add an external rel."""
    # noopener for security reasons
    # nofollow to disincentivize arXiv articles for SEO
    # external says that link is away from arxiv
    attrs[(None, "rel")] = "external noopener nofollow"
    _extend_class_attr(attrs, "link-external")
    return attrs


def _add_rel_internal(attrs: Attrs, new: bool = False) -> Attrs:
    """Add an internal rel."""
    _extend_class_attr(attrs, "link-internal")
    return attrs


def _this_url_text(attrs: Attrs, new: bool = False) -> Attrs:
    o = urlparse(attrs[(None, "href")])
    if o.hostname and not o.hostname.endswith("arxiv.org"):
        attrs["_text"] = f"this {o.scheme} URL"  # Replaces the link text.
    return attrs


def _add_scheme_info(attrs: Attrs, new: bool = False) -> Attrs:
    o = urlparse(attrs[(None, "href")])
    if (None, "class") not in attrs:
        attrs[(None, "class")] = ""
    _extend_class_attr(attrs, f"link-{o.scheme}")
    return attrs


def _handle_arxiv_url(attrs: Attrs, new: bool = False) -> Attrs:
    """
    Screen for reference to an arXiv e-print, and generate URL.

    If the :ref:`.ARXIV_ID` pattern is used, it will generate a link with the
    identifier as a the target. We need to intercept these links, and generate
    a real URL.
    """
    href = attrs[(None, "href")]
    if "://" in href:  # http://1902.00123
        target = href.split("://", 1)[1]
        prefix = ""
    elif ":" in href:  # arxiv:1902.00123
        target = href.split(":", 1)[1]
        prefix = "arXiv:"
    else:
        target = href
        prefix = ""
    if ARXIV_ID.match(target):
        attrs[(None, "href")] = arxiv_id_to_url(target)
        attrs["_text"] = f"{prefix}{target}"
        attrs[(None, "data-arxiv-id")] = target  # Add arxiv="<arxiv id>"
    return attrs


def _handle_doi_url(attrs: Attrs, new: bool = False) -> Attrs:
    """
    Screen for reference to a DOI, and generate a URL.

    If the :ref:`.DOI` pattern is used, it will generate a link with the
    doi as a the target. We need to intercept these links, and generate
    a real URL.
    """
    href = attrs[(None, "href")]
    if "://" in href:
        target = href.split("://", 1)[1]
        prefix = ""
    elif ":" in href:
        target = href.split(":", 1)[1]
        prefix = "doi:"
    else:
        target = href
        prefix = ""
    if DOI.match(target):
        doi_url = url_for_doi(target)
        attrs[(None, "href")] = doi_url
        attrs["_text"] = doi_url
        attrs[(None, "data-doi")] = target  # Add arxiv="<arxiv id>"
    return attrs


def _handle_broad_doi_url(attrs: Attrs, new: bool = False) -> Attrs:
    """
    Handle doi from DOI field.

    It is always just a DOI so turn it into a DOI link.
    """
    doi_attrs = _handle_doi_url(attrs, new)
    if (None, "data-doi") in doi_attrs:
        return doi_attrs
    else:
        target = attrs["_text"]
        doi_url = url_for_doi(target)
        attrs[(None, "href")] = doi_url
        attrs[(None, "data-doi")] = target
        return attrs


ENDS_WITH_TLD = r".*\.(" + TLDS + ")$"
CATEGORIES_THAT_COULD_BE_HOSTNAMES = "|".join(
    [
        cat_id
        for cat_id in CATEGORIES.keys()
        if re.search(ENDS_WITH_TLD, cat_id, re.IGNORECASE)
    ]
)
DONT_URLIZE_CATS = re.compile(
    CATEGORIES_THAT_COULD_BE_HOSTNAMES, re.IGNORECASE | re.UNICODE
)


def _dont_urlize_arxiv_categories(attrs: Attrs, new: bool = False) -> Attrs:
    """
    Prevent urlizing archive categories that look like hostnames.

    Ex. don't urlize math.CO but do urlize supermath.co
    """
    url = urlparse(attrs[(None, "href")])
    if DONT_URLIZE_CATS.match(url.netloc):
        return None  # type: ignore
    else:
        return attrs


PATTERNS = {"doi": DOI, "doi_field": BROAD_DOI, "url": URL, "arxiv_id": ARXIV_ID}
ORDER = ["arxiv_id", "doi", "url", "doi_field"]
DEFAULT_KINDS = ["arxiv_id", "doi", "url"]
"""Default list of identifier types to match and convert to to URLs.

This does not include 'doi_field because that is a specialized kind
for just the abs DOI field."""

callbacks = {
    "doi": [_handle_doi_url, _add_scheme_info, _add_rel_external],
    "doi_field": [_handle_broad_doi_url, _add_scheme_info, _add_rel_external],
    "arxiv_id": [_handle_arxiv_url, _add_scheme_info],
    "url": [_dont_urlize_arxiv_categories, _this_url_text, _add_rel, _add_scheme_info],
}
"""Bleach attribute callbacks for each kind."""


def _get_pattern(kinds: List[str]) -> Pattern:
    return re.compile(
        "|".join(
            [
                rf"(?:{PATTERNS[kind].pattern})"
                for kind in sorted(kinds, key=lambda kind: ORDER.index(kind))
            ]
        ),
        re.IGNORECASE | re.VERBOSE | re.UNICODE,
    )


def _get_linker_of_kind(kind: str) -> Callable_Linker:
    # The returned object will attempt to match url_re in the input string.
    # For each url_re that matches, it will run all of the attribute
    # adjusting callbacks and then stick the tag in the output string
    # replacing the matched text.
    linker: Callable[[str], str] = bleach.linkifier.Linker(
        callbacks=callbacks[kind], skip_tags=["a"], url_re=_get_pattern([kind])
    ).linkify
    return linker


def _compose_list_of_funcs(fv: List[Callable_Linker]) -> Callable_Linker:
    """Return function that calls fv functions one after another."""
    if not fv:
        return lambda x: x
    return reduce(lambda f, g: lambda x: f(g(x)), fv[1:], fv[0])


def _deferred_thread_local_linker_of_kind(kind: str) -> Callable_Linker:
    # Bleach linkifiers are not thread safe. This puts them on Flask.g.
    #
    # This will return a Callable that creates the bleach linkifier
    # only when called with the string to linkify. This is so the
    # bleach linkifier can be put into a Flask.g of each
    # individual WSGI thread.

    def deferred(instr: str) -> str:
        # This must not be called while the app is starting up, only
        # when the linkiers are being used in requests. So the
        # function is created/cached at call time.
        if "linkers" not in g:
            g.linkers = {}
        if kind not in g.linkers:
            g.linkers[kind] = _get_linker_of_kind(kind)

        return g.linkers[kind](instr)  # type: ignore

    return deferred


def _get_linker(kinds: List[str]) -> Callable_Linker:
    # Gets composed, thread-local, deferred linkers.
    # This is intended to be run as the flask app starts up
    # or in the loading of packages.
    # The actual creating of thread local bleach objects is
    # done in _deferred_thread_local_linker_of_kind.
    if len(kinds) > 1 and "doi_field" in kinds:
        raise ValueError("doi_field should not be used in combination with other kinds")
    ordered_linkers = [
        _deferred_thread_local_linker_of_kind(kind)
        for kind in sorted(kinds, key=lambda kind: ORDER.index(kind))
    ]
    return _compose_list_of_funcs(ordered_linkers)


def urlize(text: str, kinds: List[str] = DEFAULT_KINDS) -> str:
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


def urlizer(kinds: List[str] = DEFAULT_KINDS) -> Callable_Linker:
    """Generate a function to convert tokens to links.

    If the urlizing function is going to be reused, this is more
    efficient than urlize because this will only call _get_linker()
    once. urlize() will call _get_linker() on each call to urlize(txt)

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
