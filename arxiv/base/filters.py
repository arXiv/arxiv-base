"""Template filters."""

import re
from functools import partial
from typing import Union
from flask import Flask
from jinja2 import Markup, escape
from arxiv.base.urls import urlize, url_for_doi, canonical_url, \
    clickthrough_url
from arxiv.util.tex2utf import tex2utf
from arxiv.taxonomy import get_category_display, get_archive_display, \
    get_group_display

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
              letters: bool = True) -> Markup:
    """Return output of tex2utf function as escaped Markup."""
    if isinstance(text, Markup):
        return escape(tex2utf(text.unescape(), letters=letters))
    else:
        return Markup(escape(tex2utf(text, letters=letters)))


def register_filters(app: Flask) -> None:
    """
    Register base template filters on a Flask app.

    Parameters
    ----------
    app : :class:`Flask`

    """
    app.template_filter('abstract_lf_to_br')(abstract_lf_to_br)
    app.template_filter('urlize')(urlize)
    app.template_filter('tex2utf')(partial(f_tex2utf, letters=True))
    app.template_filter('tex2utf_no_symbols')(partial(f_tex2utf, letters=False))
    app.template_filter('canonical_url')(canonical_url)
    app.template_filter('clickthrough_url')(clickthrough_url)
    app.template_filter('get_category_display')(get_category_display)
    app.template_filter('get_archive_display')(get_archive_display)
    app.template_filter('get_group_display')(get_group_display)
