"""Flask configuration."""

import os

SERVER_NAME = None

ARXIV_TWITTER_URL = os.environ.get('ARXIV_TWITTER_URL',
                                   'https://twitter.com/arxiv')
ARXIV_SEARCH_BOX_URL = os.environ.get('SEARCH_BOX_URL', '/search')
ARXIV_SEARCH_ADVANCED_URL = os.environ.get('ARXIV_SEARCH_ADVANCED_URL',
                                           '/search/advanced')
ARXIV_ACCOUNT_URL = os.environ.get('ACCOUNT_URL', '/user')
ARXIV_LOGIN_URL = os.environ.get('LOGIN_URL', '/user/login')
ARXIV_LOGOUT_URL = os.environ.get('LOGOUT_URL', '/user/logout')
ARXIV_HOME_URL = os.environ.get('ARXIV_HOME_URL', 'https://arxiv.org')
ARXIV_HELP_URL = os.environ.get('ARXIV_HELP_URL', '/help')
ARXIV_CONTACT_URL = os.environ.get('ARXIV_CONTACT_URL', '/help/contact')
ARXIV_BLOG_URL = os.environ.get('ARXIV_BLOG_URL',
                                "https://blogs.cornell.edu/arxiv/")
ARXIV_WIKI_URL = os.environ.get(
    'ARXIV_WIKI_URL',
    "https://confluence.cornell.edu/display/arxivpub/arXiv+Public+Wiki"
)
ARXIV_ACCESSIBILITY_URL = os.environ.get(
    'ARXIV_ACCESSIBILITY_URL',
    "mailto:web-accessibility@cornell.edu"
)
ARXIV_LIBRARY_URL = os.environ.get('ARXIV_LIBRARY_URL',
                                   'https://library.cornell.edu')
ARXIV_ACKNOWLEDGEMENT_URL = os.environ.get(
    'ARXIV_ACKNOWLEDGEMENT_URL',
    "https://confluence.cornell.edu/x/ALlRF"
)

ARXIV_BUSINESS_TZ = os.environ.get('ARXIV_BUSINESS_TZ', 'US/Eastern')
