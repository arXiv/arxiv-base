from typing import List, Optional, Tuple

import pytest

from arxiv.formats.html import post_process_html, pre_process_html
from arxiv.identifier import Identifier

BASE = 'https://submit.example.org/1/preview/html/'
BASE_TAG = b'<base href="https://submit.example.org/1/preview/html/" />'
STAMP_TAG = b'<address><p>S</p></address>'


def _pre_process(html: bytes) -> bytes:
    return pre_process_html(html, base_url=BASE, stamp='S', link_site='arxiv.org')


def test_pre_process_html_replaces_user_base_href() -> None:
    html = (b'<html><head><base href="http://example.com/"><title>T</title>'
            b'</head><body class="x">text</body></html>')
    assert _pre_process(html) == (
        b'<html><head>' + BASE_TAG + b'<title>T</title></head><body class="x">'
        + STAMP_TAG + b'text</body></html>')


@pytest.mark.parametrize('html, expected', [
    (b'<title>T</title><p>x</p>',
     b'<title>T</title>' + STAMP_TAG + BASE_TAG + b'<p>x</p>'),
    (b'<html><p>x</p></html>',
     b'<html>' + STAMP_TAG + BASE_TAG + b'<p>x</p></html>'),
    (b'<p>x</p>',
     STAMP_TAG + b'\n' + BASE_TAG + b'\n<p>x</p>'),
])
def test_pre_process_html_falls_back_like_legacy(html: bytes, expected: bytes) -> None:
    """Without <head> or <body>, legacy inserts after </title> or <html>,
    else at the top."""
    assert _pre_process(html) == expected


def test_pre_process_html_makes_absolute_links_relative() -> None:
    html = (b'<body><img src="/figs/a.png"><img src="//cdn.example.com/b.png">'
            b'<a href="/c.html">c</a></body>')
    out = _pre_process(html)
    assert b'src="figs/a.png"' in out
    assert b'src="cdn.example.com/b.png"' in out
    assert b'href="c.html"' in out


def test_pre_process_html_rewrites_old_arxiv_hosts() -> None:
    html = b'<body><a href="http://xxx.lanl.gov/abs/hep-th/9901001">x</a></body>'
    assert b'href="http://arxiv.org/abs/hep-th/9901001"' in _pre_process(html)


class Listings:
    """A listing callback that records what it was asked for."""

    def __init__(self, known: bool = True) -> None:
        self.known = known
        self.calls: List[Tuple[str, bool]] = []

    def __call__(self, arxiv_id: Identifier, include_abstract: bool) -> Optional[str]:
        self.calls.append((arxiv_id.idv, include_abstract))
        return f'<dt>{arxiv_id.idv}</dt>\n' if self.known else None


def test_post_process_html_leaves_other_lines_alone() -> None:
    listing = Listings()
    for line in (b'', b'<p>x</p>\n', b'  LIST:arXiv:1203.3462\n',
                 b'<p>see LIST:arXiv:1203.3462</p>\n'):
        assert post_process_html(line, listing) == line
    assert listing.calls == []


@pytest.mark.parametrize('line, idv', [
    (b'LIST:1203.3462\n', '1203.3462'),
    (b'LIST:arXiv:1203.3462v1\n', '1203.3462v1'),
    (b'LIST:hep-th/9901001\n', 'hep-th/9901001'),
    (b'LIST:math.CA/0611800v2 trailing text\n', 'math/0611800v2'),
])
def test_post_process_html_lists_the_paper(line: bytes, idv: str) -> None:
    listing = Listings()
    assert post_process_html(line, listing) == f'<dl>\n<dt>{idv}</dt>\n</dl>\n'.encode()
    assert listing.calls == [(idv, False)]


@pytest.mark.parametrize('line, include_abstract', [
    (b'ABS:1203.3462\n', True),
    (b'abs:1203.3462\n', False),  # as in legacy
])
def test_post_process_html_abs_includes_the_abstract(line: bytes, include_abstract: bool) -> None:
    listing = Listings()
    post_process_html(line, listing)
    assert listing.calls == [('1203.3462', include_abstract)]


@pytest.mark.parametrize('line', [b'LIST:1203.3462\n', b'LIST:1313.00001\n'])
def test_post_process_html_leaves_unknown_papers_alone(line: bytes) -> None:
    assert post_process_html(line, Listings(known=False)) == line


def test_post_process_html_links_report_numbers() -> None:
    line = b'  REPORT-NO:SampleWS/2026/01\n'
    assert post_process_html(line, Listings()) == (
        b'<a href="/search/?searchtype=report_num&query=SampleWS%2F2026%2F01">'
        b'SampleWS/2026/01</a>\n')
    assert post_process_html(line, Listings(), search_url='https://arxiv.org/search/') == (
        b'<a href="https://arxiv.org/search/?searchtype=report_num&query=SampleWS%2F2026%2F01">'
        b'SampleWS/2026/01</a>\n')
