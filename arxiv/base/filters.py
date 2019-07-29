"""Template filters."""

import re
import os
from functools import partial
from datetime import datetime
from pytz import timezone
from typing import Union

from flask import Flask
from jinja2 import Markup, escape

from arxiv.base.urls import urlizer, canonical_url, clickthrough_url
from arxiv.util.tex2utf import tex2utf
from arxiv.taxonomy import get_category_display, get_archive_display, \
    get_group_display

ET = timezone('US/Eastern')


JinjaFilterInput = Union[Markup, str]
"""
   Jinja filters will receive their text input as either
   a Markup object or a str. It is critical for proper escaping to
   to ensure that str is correctly HTML escaped.

   Markup is decoded from str so this type is redundant but
   the hope is to make it clear what is going on to arXiv developers.
"""


def abstract_lf_to_br(text: JinjaFilterInput) -> Markup:
    """Lines that start with two spaces should be broken."""
    if isinstance(text, Markup):
        etxt = text
    else:
        etxt = Markup(escape(text))

    # if line starts with spaces, replace the white space with <br />
    br = re.sub(r'((?<!^)\n +)', '\n<br />', etxt)
    dedup = re.sub(r'\n\n', '\n', br)  # skip if blank
    return Markup(dedup)


def f_tex2utf(text: JinjaFilterInput,
              greek: bool = True) -> Markup:
    """Return output of tex2utf function as escaped Markup."""
    if isinstance(text, Markup):
        return escape(tex2utf(text.unescape(), greek=greek))
    else:
        return Markup(escape(tex2utf(text, greek=greek)))


def embed_content(path: str) -> Markup:
    """Embed the content of a static file."""
    stat = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
    with open(os.path.join(stat, path)) as f:
        return Markup(f.read())


def tidy_filesize(size: Union[int, float]) -> str:
    """
    Convert upload size to human readable form.

    Decision to use powers of 10 rather than powers of 2 to stay compatible
    with Jinja filesizeformat filter with binary=false setting that we are
    using in file_upload template.

    Parameter: size in bytes
    Returns: formatted string of size in units up through GB

    """
    units = ["B", "KB", "MB", "GB"]
    if size == 0:
        return "0B"
    if size > 1000000000:
        return '{} {}'.format(size, units[3])
    units_index = 0
    while size > 1000:
        units_index += 1
        size = round(size / 1000, 3)
    return '{} {}'.format(size, units[units_index])


def as_eastern(utc_datetime: datetime) -> datetime:
    """Relocalize an UTC datetime in US/Eastern time."""
    return utc_datetime.astimezone(ET)


def register_filters(app: Flask) -> None:
    """
    Register base template filters on a Flask app.

    Parameters
    ----------
    app : :class:`Flask`

    """
    app.template_filter('abstract_lf_to_br')(abstract_lf_to_br)
    app.template_filter('urlize')(urlizer())
    app.template_filter('tex2utf')(partial(f_tex2utf, greek=True))
    app.template_filter('tex2utf_no_symbols')(partial(f_tex2utf, greek=False))
    app.template_filter('canonical_url')(canonical_url)
    app.template_filter('clickthrough_url')(clickthrough_url)
    app.template_filter('get_category_display')(get_category_display)
    app.template_filter('get_archive_display')(get_archive_display)
    app.template_filter('get_group_display')(get_group_display)
    app.template_filter('embed_content')(embed_content)
    app.template_filter('tidy_filesize')(tidy_filesize)
    app.template_filter('as_eastern')(as_eastern)
    app.template_filter('abs_doi_to_urls')(urlizer(['doi_field']))
    app.template_filter('arxiv_id_urlize')(urlizer(['arxiv_id']))
