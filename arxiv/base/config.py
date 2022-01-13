"""Flask configuration."""

from typing import Optional
import os
from urllib.parse import urlparse
from arxiv.release.dist_version import get_version

SERVER_NAME = None

SECRET_KEY = os.environ.get("SECRET_KEY", "yes123")
A11Y_URL = os.environ.get(
    "ARXIV_ACCESSIBILITY_URL", "mailto:web-accessibility@cornell.edu"
)

EXTERNAL_URL_SCHEME = os.environ.get("EXTERNAL_URL_SCHEME", "https")
BASE_SERVER = os.environ.get("BASE_SERVER", "arxiv.org")

URLS = [
    ("help", "/help", BASE_SERVER),
    ("help_identifier", "/help/arxiv_identifier", BASE_SERVER),
    ("help_trackback", "/help/trackback", BASE_SERVER),
    ("help_mathjax", "/help/mathjax", BASE_SERVER),
    ("help_social_bookmarking", "/help/social_bookmarking", BASE_SERVER),
    ("contact", "/help/contact", BASE_SERVER),
    ("search_box", "/search", BASE_SERVER),
    ("search_archive", "/search/<archive>", BASE_SERVER),
    ("search_advanced", "/search/advanced", BASE_SERVER),
    ("account", "/user", BASE_SERVER),
    ("login", "/login", BASE_SERVER),
    ("logout", "/logout", BASE_SERVER),
    ("home", "/", BASE_SERVER),
    ("ignore_me", "/IgnoreMe", BASE_SERVER),  # Anti-robot honneypot.
    ("pdf", "/pdf/<arxiv:paper_id>", BASE_SERVER),
    ("twitter", "/arxiv", "twitter.com"),
    ("blog", "/arxiv", "blogs.cornell.edu"),
    ("wiki", "/display/arxivpub/arXiv+Public+Wiki", "confluence.cornell.edu"),
    ("library", "/", "library.cornell.edu"),
    ("university", "/", "cornell.edu"),
    ("acknowledgment", "/about/ourmembers", BASE_SERVER),
    ("faq", "/help/faq", BASE_SERVER),
    ("subscribe", "/help/subscribe", BASE_SERVER),
    ("submit", "/submit", BASE_SERVER),
    ("about", "/about", BASE_SERVER),
    ("team", "/about/people/leadership_team", BASE_SERVER),
    ("privacy_policy", "/help/policies/privacy_policy", BASE_SERVER),
    ("copyright", "/help/license", BASE_SERVER),
    ("a11y", "/help/web_accessibility", BASE_SERVER),
    ("abs", "/abs/<arxiv:paper_id>v<string:version>", BASE_SERVER),
    ("abs_by_id", "/abs/<arxiv:paper_id>", BASE_SERVER),
    ("clickthrough", "/ct", BASE_SERVER),
]
"""
URLs for external services, for use with :func:`flask.url_for`.

For details, see :mod:`arxiv.base.urls`.
"""

# In order to provide something close to the config_url behavior, this will
# look for ARXIV_{endpoint}_URL variables in the environ, and update `URLS`
# accordingly.
for key, value in os.environ.items():
    if key.startswith("ARXIV_") and key.endswith("_URL"):
        endpoint = "_".join(key.split("_")[1:-1]).lower()
        o = urlparse(value)
        if not o.netloc:  # Doesn't raise an exception.
            continue
        i: Optional[int]
        try:
            i = list(zip(*URLS))[0].index(endpoint)
        except ValueError:
            i = None
        if i is not None:
            URLS[i] = (endpoint, o.path, o.netloc)

ARXIV_BUSINESS_TZ = os.environ.get("ARXIV_BUSINESS_TZ", "US/Eastern")

BASE_VERSION = get_version('arxiv-base')
"""The version of the arxiv-base package."""

APP_VERSION = get_version('arxiv-base')
"""The version of the base test app. This is used to build the paths
to static assets, see :mod:`arxiv.base`."""

"""
Flask-S3 plugin settings.

See `<https://flask-s3.readthedocs.io/en/latest/>`_.
"""
FLASKS3_BUCKET_NAME = os.environ.get("FLASKS3_BUCKET_NAME", "some_bucket")
# FLASKS3_CDN_DOMAIN = os.environ.get('FLASKS3_CDN_DOMAIN', 'static.arxiv.org')
FLASKS3_USE_HTTPS = os.environ.get("FLASKS3_USE_HTTPS", 1)
FLASKS3_FORCE_MIMETYPE = os.environ.get("FLASKS3_FORCE_MIMETYPE", 1)
FLASKS3_ACTIVE = bool(int(os.environ.get("FLASKS3_ACTIVE", 0)))

# AWS credentials.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "nope")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "nope")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# In some cases, we want an app to handle all of its static files, e.g. when
# deploying in a development environment. Setting the configuration param
# RELATIVE_STATIC_PATHS to True will cause ``/{RELATIVE_STATIC_PREFIX}`` to be
# prepended to the static paths for base assets. This should have no impact on
# static paths for blueprints.
RELATIVE_STATIC_PATHS = bool(int(os.environ.get("RELATIVE_STATIC_PATHS", "0")))
RELATIVE_STATIC_PREFIX = os.environ.get("RELATIVE_STATIC_PREFIX", "")

ANALYTICS_ENABLED = bool(int(os.environ.get("ANALYTICS_ENABLED", "0")))
"""Enable/disable Matomo web analytics."""
ANALYTICS_BASE_URL = os.environ.get("ANALYTICS_BASE_URL", "https://webstats.arxiv.org/")
"""Base URL for analytics tracker. Should include trailing slash."""
ANALYTICS_COOKIE_DOMAIN = os.environ.get("ANALYTICS_COOKIE_DOMAIN", "*.arxiv.org")
"""Analytics tracker cookie domain."""
ANALYTICS_SITE_ID = os.environ.get("ANALYTICS_SITE_ID", "1")
"""Analytics tracker site ID."""
