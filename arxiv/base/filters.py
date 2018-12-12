"""Template filters."""

from flask import Flask
from arxiv.base.urls import urlize, canonical_url
from arxiv.util.tex2utf import tex2utf


def register_filters(app: Flask) -> None:
    app.template_filter('urlize')(urlize)
    app.template_filter('tex2utf')(tex2utf)
    app.template_filter('canonical_url')(canonical_url)
