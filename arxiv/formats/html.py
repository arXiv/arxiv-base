"""Processing of papers whose source is HTML.

Ports of legacy's ``arXiv::HTML::src2html`` (arxiv-lib), shared so that a
submission's HTML preview is processed as its announced paper will be.
"""
import logging
import re
from typing import Callable, List, Optional
from urllib.parse import quote

from ..identifier import Identifier, IdentifierException

logger = logging.getLogger(__name__)

LAX_ID_REGEX = rb'(arXiv:)?([a-z-]+(\.[A-Z][A-Z])?/\d{7}|\d{4}\.\d{4,5})(v\d+)?'
"""An arXiv ID as a ``LIST:`` or ``ABS:`` line may give it."""

_LIST_LINE = re.compile(rb'(LIST|ABS):(' + LAX_ID_REGEX + rb')', re.I)
_REPORT_NO_LINE = re.compile(rb'\s*REPORT-NO:([A-Za-z0-9-/]+)', re.I)


def pre_process_html(html: bytes, base_url: str, stamp: str, link_site: str) -> bytes:
    """Prepare an HTML page to be served from ``base_url``.

    Port of legacy's ``pre_process_html``: points old arXiv hosts at
    ``link_site``, swaps any user ``<base>`` for ``base_url``, inserts the
    stamp, and makes absolute ``src``/``href`` paths relative so they resolve
    inside the paper. Like legacy, it works on the raw bytes with regular
    expressions and leaves scripts alone.
    """
    base = f'<base href="{base_url}" />'.encode()
    stamp_tag = f'<address><p>{stamp}</p></address>'.encode()
    html = re.sub(rb'xxx\.lanl\.gov|arxiv\.org', link_site.encode(), html, flags=re.I)
    html = re.sub(rb'<base\s+href=[^>]*>', b'', html, count=1, flags=re.I | re.S)
    html = _insert_after([rb'<head>', rb'</title>', rb'<html>'], base, html)
    html = _insert_after([rb'<body[^>]*>', rb'</head>', rb'</title>', rb'<html>'],
                         stamp_tag, html)
    for attr in (b'src', b'href'):
        for pattern in (attr + rb'\s*=\s*"/(\S+)"', attr + rb'\s*=\s*/(\S+)'):
            count = 1
            while count:
                html, count = re.subn(pattern, attr + rb'="\1"', html, flags=re.I | re.S)
    return html


def post_process_html(line: bytes,
                      listing: Callable[[Identifier, bool], Optional[str]],
                      search_url: str = '/search/') -> bytes:
    """Expand one line of an HTML page.

    Port of legacy's ``post_process_html``. A line starting ``LIST:<id>`` or
    ``ABS:<id>`` becomes that paper's listing, with its abstract for ``ABS``.
    ``listing(arxiv_id, include_abstract)`` returns the paper's ``<dt>`` and
    ``<dd>``, or ``None`` to leave the line as it is. A line starting
    ``REPORT-NO:<number>`` becomes a link to the report-number search at
    ``search_url``. Conference indexes list their papers this way (arxiv-docs
    ``help/submit_index``).
    """
    if match := _LIST_LINE.match(line):
        try:
            arxiv_id = Identifier(match.group(2).decode())
        except IdentifierException as ee:
            logger.error("Source of html paper had a problem during post_process_html: %s", ee)
            return line
        # As in legacy, only an upper-case ABS includes the abstract.
        item = listing(arxiv_id, match.group(1) == b'ABS')
        return line if item is None else f'<dl>\n{item}</dl>\n'.encode()
    if match := _REPORT_NO_LINE.match(line):
        number = match.group(1).decode()
        return (f'<a href="{search_url}?searchtype=report_num'
                f'&query={quote(number, safe="")}">{number}</a>\n').encode()
    return line


def _insert_after(patterns: List[bytes], insert: bytes, html: bytes) -> bytes:
    """Insert after the first pattern that matches, else at the top."""
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            return html[:match.end()] + insert + html[match.end():]
    return insert + b'\n' + html
