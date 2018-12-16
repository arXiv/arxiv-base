"""Template filters."""

from flask import Flask
from arxiv.base.urls import urlize, canonical_url
from arxiv.util.tex2utf import tex2utf
from arxiv.taxonomy import get_category_display, get_archive_display, \
    get_group_display


def register_filters(app: Flask) -> None:
    app.template_filter('urlize')(urlize)
    app.template_filter('tex2utf')(tex2utf)
    app.template_filter('canonical_url')(canonical_url)
    app.template_filter('get_category_display')(get_category_display)
    app.template_filter('get_archive_display')(get_archive_display)
    app.template_filter('get_group_display')(get_group_display)
