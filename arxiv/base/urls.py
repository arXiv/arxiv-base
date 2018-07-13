"""Helpers for working with URLs in arXiv Flask applications."""

import sys
from typing import Dict, Any
from urllib.parse import parse_qs
from werkzeug.urls import url_encode, url_parse, url_unparse, url_encode
from werkzeug.routing import Map, Rule, BuildError
from flask import current_app
from arxiv.base import config
from arxiv.base.exceptions import ConfigurationError
from arxiv.base.converter import ArXivConverter


def config_url(target: str, path_params: dict = {}, params: dict = {}) -> str:
    """
    Generate a URL from this app's configuration.

    This will load the value of the configuration parameter
    `ARXIV_{target}_URL` from either the current application configuration
    (preferred), or the base configuration defined in this package (see
    :mod:`arxiv.base.config`).

    Note: this function relies on the `flask.current_app` proxy object, which
    means that it can only be used in an application or request context.

    Parameters
    ----------
    target : str
        Name of the endpoint, defined as `ARXIV_{target}_URL` in the
        application configuration.
    path_params : dict
        Parameters used to format the URL. For example, if the value of the
        configuration parameter is `http://arxiv.org/abs/{arxiv_id}/`,
        passing `path_params = {'arxiv_id': '1901.00123'}` would generate the
        URL `http://arxiv.org/abs/1901.00123`.
    params : dict
        GET request parameters to add to the URL.

    Returns
    -------
    str

    Raises
    ------
    :class:`.ConfigurationError`
        Raised if the configuration parameter for `target` cannot be found.

    Examples
    --------

    .. code-block:: python

       from arxiv.base.urls import config_url
    """
    url: str
    # Look for the URL on the config of the current app (this will *not* be
    # base); fall back to the base config if not found.
    configured_urls = dict(current_app.config.get('EXTERNAL_URLS', []))
    base_urls = dict(config.EXTERNAL_URLS)
    try:
        if configured_urls:
            url = configured_urls[target]
        else:   # Keeping this here for backward compatibility.
            url = current_app.config[f'ARXIV_{target.upper()}_URL']
    except KeyError as e:   # Not defined on the application config.
        # Fall back to the base configuration.
        url = base_urls.get(target)
        if not url:     # Nothing left to do.
            raise ConfigurationError(f'URL for {target} not set') from e

    # Format with path parameters.
    try:
        url = url.format(**path_params)
    except KeyError as e:
        raise ValueError('Missing a required parameter: %s' % e) from e

    # Format with request parameters. This uses url_parse/url_unparse to
    # modify the request ("query") parameters safely; i.e. without clobbering
    # any parameters that may already be present.
    parts = url_parse(url)
    params.update(parse_qs(parts.query))
    parts = parts.replace(query=url_encode(params))
    url = url_unparse(parts)
    return url


def get_url_map() -> str:
    """Build a :class:`werkzeug.routing.Map` from configured URLs."""
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

    ``URLS`` should be a list of two-tuples, with the name of the
    """
    values.pop('_external', None)
    url_map = get_url_map()
    adapter = url_map.bind('arxiv.org', url_scheme='https')
    return adapter.build(endpoint, values=values, force_external=True)


def external_url_handler(err: BuildError, endpoint: str, values: Dict) -> str:
    """Attempt to handle failed URL building with :func:`external_url_for`."""
    try:
        url = external_url_for(endpoint, **values)
    except BuildError as e:
        # Re-raise the original BuildError, in context of original traceback.
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is err:
            raise exc_type(exc_value).with_traceback(tb)
        else:
            raise err
    return url
