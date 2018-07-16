"""Flask configuration."""

from typing import Optional
import os
from urllib.parse import urlparse

SERVER_NAME = None

A11Y_URL = os.environ.get("ARXIV_ACCESSIBILITY_URL",
                          "mailto:web-accessibility@cornell.edu")

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
    ("twitter", "/arxiv", "twitter.com"),
    ("blog", "/arxiv", "blogs.cornell.edu"),
    ("wiki", "/display/arxivpub/arXiv+Public+Wiki", "confluence.cornell.edu"),
    ("library", "/", "library.cornell.edu"),
    ("acknowledgment", "/x/ALlRF", "confluence.cornell.edu")
]
"""
URLs for external services, for use with :func:`flask.url_for`.

For details, see :mod:`arxiv.base.urls`.
"""

# In order to provide something close to the config_url behavior, this will
# look for ARXIV_{endpoint}_URL variables in the environ, and update `URLS`
# accordingly.
for key, value in os.environ.items():
    if key.startswith('ARXIV_') and key.endswith('_URL'):
        endpoint = "_".join(key.split('_')[1:-1]).lower()
        o = urlparse(value)
        if not o.netloc:    # Doesn't raise an exception.
            continue
        i: Optional[int]
        try:
            i = list(zip(*URLS))[0].index(endpoint)
        except ValueError:
            i = None
        if i is not None:
            URLS[i] = (endpoint, o.path, o.netloc)

ARXIV_BUSINESS_TZ = os.environ.get("ARXIV_BUSINESS_TZ", "US/Eastern")
