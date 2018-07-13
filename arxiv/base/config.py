"""Flask configuration."""

import os

SERVER_NAME = None

EXTERNAL_URLS = [
    ("twitter", os.environ.get("ARXIV_TWITTER_URL",
                               "https://twitter.com/arxiv")),
    ("blog", os.environ.get("ARXIV_BLOG_URL",
                            "https://blogs.cornell.edu/arxiv/")),
    ("wiki", os.environ.get("ARXIV_WIKI_URL",
                            "https://confluence.cornell.edu/display/arxivpub/"
                            "arXiv+Public+Wiki")),
    ("accessibility", os.environ.get("ARXIV_ACCESSIBILITY_URL",
                                     "mailto:web-accessibility@cornell.edu")),
    ("library", os.environ.get("ARXIV_LIBRARY_URL",
                               "https://library.cornell.edu")),
    ("acknowledgment", os.environ.get(
        "ARXIV_ACKNOWLEDGEMENT_URL",
        "https://confluence.cornell.edu/x/ALlRF"
    )),
]
"""External URLs, configurable via environment variables."""

URLS = [
    ("help", "/help", "arxiv.org"),
    ("contact", "/help/contact", "arxiv.org"),
    ("search_box", "/search", "arxiv.org"),
    ("search_advanced", "/search/advanced", "arxiv.org"),
    ("account", "/user", "arxiv.org"),
    ("login", "/user/login", "arxiv.org"),
    ("logout", "/user/logout", "arxiv.org"),
    ("home", "/", "arxiv.org"),
    ("pdf", "/pdf/<arxiv:paper_id>", "arxiv.org"),
]
"""
URLs for other services, for use with :func:`flask.url_for`.

This only works for services at the same hostname, since Flask uses the
hostname on the request to generate the full URL. For addresses at a different
hostname, use :func:`arxiv.base.urls.config_url`, which relies on
``EXTERNAL_URLS`` in this configuration file.
"""

ARXIV_BUSINESS_TZ = os.environ.get("ARXIV_BUSINESS_TZ", "US/Eastern")
