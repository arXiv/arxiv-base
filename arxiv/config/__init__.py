"""Flask configuration."""
import importlib.metadata
from typing import Optional, List, Tuple
import os
from sqlalchemy.engine.interfaces import IsolationLevel
from secrets import token_hex
from urllib.parse import urlparse
from pydantic import SecretStr
from pydantic_settings import BaseSettings

DEFAULT_DB = "sqlite:///tests/data/browse.db"
DEFAULT_LATEXML_DB = "sqlite:///tests/data/latexml.db"

class Settings(BaseSettings):

    SERVER_NAME: Optional[str] = None
    """The name and port number of the server. Required for subdomain support
    (e.g.: 'myapp.dev:5000') Note that localhost does not support subdomains so
    setting this to "localhost" does not help. Setting a SERVER_NAME also by
    default enables URL generation without a request context but with an
    application context.

    If this is set and the Host header of a request does not match the
    SERVER_NAME, then Flask will respond with a 404. Test with curl
    http://127.0.0.1:5000/
    -sv -H "Host: subdomain.arxiv.org"
    """

    SECRET_KEY: str = "qwert2345"

    ARXIV_ACCESSIBILITY_URL: str = "mailto:web-accessibility@cornell.edu"

    EXTERNAL_URL_SCHEME: str = "https"
    BASE_SERVER: str = "arxiv.org"

    AUTH_SERVER: str = BASE_SERVER
    """Hostname for auth paths like /login and /logout.

    Usually the same as BASE_SERVER but can be configured.
    """

    SEARCH_SERVER: str = BASE_SERVER
    """Hostname for search paths.

    Usually the same as BASE_SERVER but can be configured.
    """

    SUBMIT_SERVER: str = BASE_SERVER
    """Hostname for submit paths.

    Usually the same as BASE_SERVER but can be configured.
    """

    CANONICAL_SERVER: str = BASE_SERVER
    """Hostname for use in canonical URLs.

    Usually the same as BASE_SERVER but can be configured.
    """

    HELP_SERVER: str = "info.arxiv.org"

    URLS: List[Tuple[str, str, str]] = [
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
    """URLs for external services, for use with :func:`flask.url_for`.

    For details, see :mod:`arxiv.base.urls`.
    """

    ARXIV_BUSINESS_TZ: str = "US/Eastern"
    """Timezone of the arxiv business offices."""

    FS_TZ: str = "US/Eastern"

    BASE_VERSION: str = importlib.metadata.version('arxiv-base')
    """The version of the arxiv-base package."""

    APP_VERSION: str = BASE_VERSION
    """The version of the base test app.

    This is used to build the paths
    to static assets, see :mod:`arxiv.base`.
    """

    # In some cases, we want an app to handle all of its static files, e.g. when
    # deploying in a development environment. Setting the configuration param
    # RELATIVE_STATIC_PATHS to True will cause ``/{RELATIVE_STATIC_PREFIX}`` to be
    # prepended to the static paths for base assets. This should have no impact on
    # static paths for blueprints.
    RELATIVE_STATIC_PATHS: bool = False
    RELATIVE_STATIC_PREFIX: str = ""

    ANALYTICS_ENABLED: bool = False
    """Enable/disable Matomo web analytics."""
    ANALYTICS_BASE_URL: str = "https://webstats.arxiv.org/"
    """Base URL for analytics tracker.

    Should include trailing slash.
    """
    ANALYTICS_COOKIE_DOMAIN: str = "*.arxiv.org"
    """Analytics tracker cookie domain."""
    ANALYTICS_SITE_ID: str = "1"
    """Analytics tracker site ID."""

    TRACKBACK_SECRET: SecretStr = SecretStr(token_hex(10))

    CLASSIC_DB_URI: str = DEFAULT_DB
    LATEXML_DB_URI: Optional[str] = DEFAULT_LATEXML_DB
    ECHO_SQL: bool = False
    CLASSIC_DB_TRANSACTION_ISOLATION_LEVEL: Optional[IsolationLevel] = None
    LATEXML_DB_TRANSACTION_ISOLATION_LEVEL: Optional[IsolationLevel] = None

    LATEXML_DB_QUERY_TIMEOUT: int = 5
    """Maximium seconds any query to the latxml DB can run.

    The statement will raise an excepton if it runs for longer than this
    time.

    This is intened to prevent a backed up latexml db from blocking arxiv-browse
    from serving pages. See ARXIVCE-2433.

    """

    REQUEST_CONCURRENCY: int = 32
    """ How many requests do we handle at once -> How many db connections should we be able to open at once """
    POOL_PRE_PING: bool = True
    """ Liveness check of sqlalchemy connections before checking out of pool """


    FASTLY_SERVICE_IDS:str='{"arxiv.org":"umpGzwE2hXfa2aRXsOQXZ4", "browse.dev.arxiv.org":"5eZxUHBG78xXKNrnWcdDO7", "export.arxiv.org": "hCz5jlkWV241zvUN0aWxg2", "rss.arxiv.org": "yPg50VJsPLwZQ5lFsD7rA1"}'
    """a dictionary of the various fastly services and their ids"""
    FASTLY_PURGE_TOKEN:str= "FASTLY_PURGE_TOKEN"


settings = Settings()
