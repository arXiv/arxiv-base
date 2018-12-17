"""
Helpers for working with URLs in arXiv Flask applications.

This module provides :func:`external_url_handler`, which is attached to Flask
application instances by :class:`arxiv.base.Base`. This leverage's Flask's
built-in hook for :class:`flask.BuildError` exception handlers, described in
the :func:`flask.url_for` documentation.

To set a URL for an external (i.e. not provided by thie application) endpoint,
define a variable called ``URLS`` in your application configuration. ``URLS``
should be a list of three-tuples, of the form (``endpoint (str)``,
``path (str)``, ``domain (str)``). Paths should use the `Werkzeug rule format
<http://werkzeug.pocoo.org/docs/0.14/routing/#rule-format>`_. For example:

.. code-block:: python

   URLS = [
       ("pdf", "/pdf/<arxiv:paper_id>", "arxiv.org"),
       ("twitter", "/arxiv", "twitter.com"),
       ("blog", "/arxiv", "blogs.cornell.edu")
   ]

You can load these urls using :func:`flask.url_for`. For example,
``url_for("pdf", paper_id="1601.00123")`` should return
``https://arxiv.org/pdf/1601.00123``.

Using environment variables
---------------------------
An alternative approach is to set the endpoint using an environment variable.
Setting ``ARXIV_FOO_URL`` will define a rule for endpoint ``foo`` using the
domain and path parsed from the variable's value. For example:

.. code-block:: python

   os.environ['ARXIV_BLOG_URL'] = 'http://blogs.cornell.edu/arxiv'


Caveats
-------
URLs can be defined in :mod:`arxiv.base.config`, in environment variables,
and in the configuration of a :class:`flask.Flask` application that uses
:class:`arxiv.base.Base`. Preference is given to each of those respective
sources with increasing priority.

This will build URLs with the ``https`` scheme by default. To use ``http``,
set ``EXTERNAL_URL_SCHEME = 'http'`` in your configuration.
"""

import sys
from typing import Dict, Any
from urllib.parse import parse_qs
from werkzeug.urls import url_encode, url_parse, url_unparse
from werkzeug.routing import Map, Rule, BuildError
from flask import current_app

from arxiv.base.exceptions import ConfigurationError
from arxiv.base.converter import ArXivConverter
from arxiv.base import logging

from .clickthrough import clickthrough_url
from .links import urlize, urlizer, url_for_doi

logger = logging.getLogger(__name__)


# The module arxiv.base.config needs to be able to load its values from
# environment variables, some of which are set by SetEnv directives in Apache.
# Those variables are not set until application execution begins, which means
# that if arxiv.base.config is imported beforehand its values will not be
# correct.
def _get_base_config() -> Any:
    from arxiv.base import config
    return config


def get_url_map() -> Map:
    """Build a :class:`werkzeug.routing.Map` from configured URLs."""
    config = _get_base_config()

    # Get the base URLs (configured in this package).
    configured_urls = {url[0]: url for url in config.URLS}
    # Privilege ARXIV_URLs set on the application config.
    current_urls = current_app.config.get('URLS', [])
    if current_urls:
        configured_urls.update({url[0]: url for url in current_urls})

    url_map = Map([
        Rule(pattern, endpoint=name, host=host, build_only=True)
        for name, pattern, host in configured_urls.values()
    ], converters={'arxiv': ArXivConverter}, host_matching=True)
    return url_map


def external_url_for(endpoint: str, **values: Any) -> str:
    """
    Like :flask`.url_for`, but builds external URLs based on the config.

    This works by loading the configuration variable ``URLS`` from
    :mod:`arxiv.base.config` and from the application on which the blueprint
    has been registered, and registering the URL patterns described therein.
    Preference is given to URLs defined on the current application. An attempt
    is made to avoid adding URL rules for which identical patterns have already
    been registered.
    """
    values.pop('_external', None)
    url_map = get_url_map()
    scheme = current_app.config.get('EXTERNAL_URL_SCHEME', 'https')
    host = current_app.config.get('BASE_SERVER', 'arxiv.org')
    adapter = url_map.bind(host, url_scheme=scheme)
    url: str = adapter.build(endpoint, values=values, force_external=True)
    return url


def external_url_handler(err: BuildError, endpoint: str, values: Dict) -> str:
    """
    Attempt to handle failed URL building with :func:`external_url_for`.

    This gets attached to a Flask application via the
    :meth:`flask.Flask.url_build_error_handlers` hook.
    """
    try:
        url = external_url_for(endpoint, **values)
    except BuildError as e:
        # Re-raise the original BuildError, in context of original traceback.
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is err:
            raise exc_type(exc_value).with_traceback(tb)    # type: ignore
        else:
            raise err
    return url


def canonical_url(id: str, version: int = 0) -> str:
    """
    Generate the canonical URL for an arXiv identifier.

    This can be done from just the ID because the category is only needed if it
    is in the ID. id can be just the id or idv or cat/id or cat/idv.
    """
    # TODO: This should be better.
    # There should probably be something like INTERNAL_URL_SCHEMA
    # Also, /abs should probably be specified somewhere else
    # like arxiv.base.canonical
    scheme = current_app.config.get('EXTERNAL_URL_SCHEME', 'https')
    host = current_app.config.get('MAIN_SERVER', 'arxiv.org')
    if version:
        return f'{scheme}://{host}/abs/{id}v{version}'
    return f'{scheme}://{host}/abs/{id}'
