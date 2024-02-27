"""Flask configuration."""
import importlib.metadata
from typing import Optional
import os
import secrets
from urllib.parse import urlparse

SERVER_NAME = None

SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(16))
A11Y_URL = os.environ.get(
    "ARXIV_ACCESSIBILITY_URL", "mailto:web-accessibility@cornell.edu"
)

EXTERNAL_URL_SCHEME = os.environ.get("EXTERNAL_URL_SCHEME", "https")
BASE_SERVER = os.environ.get("BASE_SERVER", "arxiv.org")

AUTH_SERVER = os.environ.get("AUTH_SERVER", BASE_SERVER)
"""Hostname for auth paths like /login and /logout.

Usually the same as BASE_SERVER but can be configured.
"""

SEARCH_SERVER = os.environ.get("SEARCH_SERVER", BASE_SERVER)
"""Hostname for search paths.

Usually the same as BASE_SERVER but can be configured.
"""

SUBMIT_SERVER = os.environ.get("SUBMIT_SERVER", BASE_SERVER)
"""Hostname for submit paths.

Usually the same as BASE_SERVER but can be configured.
"""

CANONICAL_SERVER = os.environ.get("CANONICAL_SERVER", BASE_SERVER)
"""Hostname for use in canonical URLs.

Usually the same as BASE_SERVER but can be configured.
"""

HELP_SERVER = os.environ.get("HELP_SERVER", "info.arxiv.org")

URLS = [
    ("a11y", "/help/web_accessibility.html", HELP_SERVER),
    ("about", "/about", HELP_SERVER),
    ("about_give", "/about/give.html", HELP_SERVER),
    ("about_people", "/about/people/index.html", HELP_SERVER),
    ("acknowledgment", "/about/ourmembers.html", HELP_SERVER),
    ("contact", "/help/contact.html", HELP_SERVER),
    ("copyright", "/help/license/index.html", HELP_SERVER),
    ("faq", "/help/faq/index.html", HELP_SERVER),
    ("help", "/help", HELP_SERVER),
    ("help_archive_description", "/help/<archive>/index.html", HELP_SERVER),
    ("help_identifier", "/help/arxiv_identifier.html", HELP_SERVER),
    ("help_mathjax", "/help/mathjax.html", HELP_SERVER),
    ("help_social_bookmarking", "/help/social_bookmarking", HELP_SERVER), # Does not resolve
    ("help_submit", "/help/submit/index.html", HELP_SERVER),
    ("help_trackback", "/help/trackback.html", HELP_SERVER),
    ("new", "/", HELP_SERVER),    # this help page might be gone, use to go to very old news
    ("privacy_policy", "/help/policies/privacy_policy.html", HELP_SERVER),
    ("subscribe", "/help/subscribe", HELP_SERVER),
    ("team", "/about/people/leadership_team.html", HELP_SERVER),

    ("abs", "/abs/<arxiv:paper_id>v<string:version>", BASE_SERVER),
    ("abs_by_id", "/abs/<arxiv:paper_id>", BASE_SERVER),
    ("pdf", "/pdf/<arxiv:paper_id>", BASE_SERVER),

    ("canonical_pdf", "/pdf/<arxiv:paper_id>v<string:version>", CANONICAL_SERVER),
    ("canonical_pdf_by_id", "/pdf/<arxiv:paper_id>", CANONICAL_SERVER),
    ("canonical_abs", "/abs/<arxiv:paper_id>v<string:version>", CANONICAL_SERVER),
    ("canonical_abs_by_id", "/abs/<arxiv:paper_id>", CANONICAL_SERVER),

    ("clickthrough", "/ct", BASE_SERVER),
    ("home", "/", BASE_SERVER),
    ("ignore_me", "/IgnoreMe", BASE_SERVER),  # Anti-robot honneypot.

    ("account", "/user", AUTH_SERVER),
    ("login", "/login", AUTH_SERVER),
    ("logout", "/logout", AUTH_SERVER),

    ("create", "/user/create", SUBMIT_SERVER),
    ("submit", "/submit", SUBMIT_SERVER),

    ("search_advanced", "/search/advanced", SEARCH_SERVER),
    ("search_archive", "/search/<archive>", SEARCH_SERVER),
    ("search_box", "/search", SEARCH_SERVER),

    ("blog", "/arxiv", "blogs.cornell.edu"),
    ("library", "/", "library.cornell.edu"),
    ("twitter", "/arxiv", "twitter.com"),
    ("university", "/", "cornell.edu"),
    ("wiki", "/display/arxivpub/arXiv+Public+Wiki", "confluence.cornell.edu"),
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

BASE_VERSION = os.environ.get("BASE_VERSION", importlib.metadata.version('arxiv-base'))
"""The version of the arxiv-base package."""

APP_VERSION = os.environ.get("APP_VERSION", BASE_VERSION)
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

TRACKBACK_SECRET = os.environ.get("TRACKBACK_SECRET", "baz")

DEFAULT_DB = "sqlite:///tests/data/browse.db"
DEFAULT_LATEXML_DB = "sqlite:///tests/data/latexml.db"

CLASSIC_DB_URI = os.environ.get("CLASSIC_DB_URI", DEFAULT_DB)
LATEXML_DB_URI = os.environ.get("LATEXML_DB_URI", DEFAULT_LATEXML_DB)
ECHO_SQL = os.environ.get("ECHO_SQL", True)