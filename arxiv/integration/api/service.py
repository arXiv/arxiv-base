"""
Provides a base class for HTTP API integrations.

The goal of this module is to handle boilerplate connection and request
handling that is invariant (or nearly so) among service integration modules
that target HTTP APIs.

.. todo::
   Make retry parameters easier to configure.


Specific goals
--------------

- Handle verifying the response status code, and raise appropriate and
  semantically meaningful exceptions.
- Handle setting up a persistent HTTP session to cut down on overhead.
- Provide basic retry functionality.
- Handle binding a service instance (with its persistent session) to the
  Flask application context.

"""

from typing import Optional, Tuple, MutableMapping, List, Any
from http import HTTPStatus as status
import inspect
import requests
from urllib3.util.retry import Retry
from urllib.parse import urlparse, urlunparse, urlencode
import json

from flask import g, Flask, current_app


from ..meta import MetaIntegration
import logging

from .exceptions import RequestFailed, RequestUnauthorized, RequestForbidden, \
    NotFound, BadRequest, SecurityException, ConnectionFailed, BadResponse

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = 'http://fooservice:8000/'
DEFAULT_VERIFY = True


class HTTPIntegration(metaclass=MetaIntegration):
    """
    Integrate with a service over HTTP.

    Provides binding to the application context, so that connections can be
    re-used.

    To implement an HTTP API service integration, define a class that inherits
    from :class:`.HTTPIntegration`. At minimum, it should include an inner
    class called ``Meta`` with the attribute ``service_name``; this is used to
    identify the configuration parameters for the service. For example:

    .. code-block:: python

       class MyCoolIntegration(HTTPIntegration):
           class Meta:
               service_name = "cool_beans"

           def get_something(self, anything: str, token: str) -> dict:
               data, _, _ = self.json("get", f"/thing/{anything}", token)
               return data


    and in your ``config.py``, include:

    .. code-block:: python

       COOL_BEANS_ENDPOINT = "http://thecool.beans.arxiv.org:9876"
       COOL_BEANS_VERIFY = False   # (or True, if you are using SSL)


    Thanks to :class:`arxiv.integration.meta.MetaIntegration`, you should be
    able to use this integration in your app like:

    .. code-block:: python

       from my.cool.services import MyCoolIntegration
       from arxiv.users import auth

       app = Flask(__name__)
       MyCoolIntegration.init_app(app)
       auth.Auth(app)

       @app.route('/foo')
       def foo():
           mci = MyCoolIntegration.current_session()
           mci.get_something('foo', request.environ['token'])
           ...


    Any additional parameters in your app config that start with the
    ``service_name`` in upper case will be passed in as kwargs to the
    constructor. By default, these are stored on ``._extra`` for internal
    use.

    """

    class Meta:
        """
        Additional info about this class.

        This should be overridden by any child class.
        """

        service_name = "base"

    default_retry_config = Retry(
        total=10,
        read=10,
        connect=10,
        status=10,
        backoff_factor=0.5
    )
    """Default retry behavior for HTTP request."""

    def __init__(self, endpoint: str, verify: bool = True,
                 headers: dict = {}, **extra: Any) -> None:
        """
        Initialize an HTTP session.

        Parameters
        ----------
        endpoint : str
            Base service URI.
        verify : bool
            Whether or not SSL certificate verification should enforced.
        headers : dict
            Headers to be included on all requests.
        extra : kwargs

        """
        self._extra = extra
        self._session = requests.Session()
        self._verify = verify
        self._retry = self.get_retry_config()
        self._adapter = requests.adapters.HTTPAdapter(max_retries=self._retry)
        self._session.mount(f'{urlparse(endpoint).scheme}://', self._adapter)
        if not endpoint.endswith('/'):
            endpoint += '/'
        self._endpoint = endpoint
        self._session.headers.update(headers)

    def get_retry_config(self) -> Retry:
        """
        Defines the retry behavior for HTTP requests.

        This is defined as an instance method so that it can be defined in
        relation to an app config or other contextual information.

        See :class:`urllib3.util.retry.Retry`.
        """
        return self.default_retry_config

    def _path(self, path: str, query: dict = {}) -> str:
        """Generate a full path for a request."""
        o = urlparse(self._endpoint)
        path = path.lstrip('/')
        return urlunparse((  # type: ignore
            o.scheme, o.netloc, f"{o.path}{path}",
            None, urlencode(query), None
        ))

    def _check_status(self, resp: requests.Response,
                      expected_code: List[int] = [status.OK]) -> None:
        """Check for unexpected or errant status codes."""
        if resp.status_code not in expected_code:
            raise_for_http_status(resp.status_code, resp)
            raise RequestFailed(f'Unexpected code: {resp.status_code}', resp)

    def _parse_location(self, location: str) -> str:
        endpoint_path = urlparse(self._endpoint).path
        if self._endpoint in location:
            _, location = location.split(self._endpoint, 1)
        elif endpoint_path in location:
            _, location = location.split(endpoint_path, 1)
        return location

    def request(self, method: str, path: str, token: Optional[str] = None,
                expected_code: List[int] = [status.OK],
                allow_2xx_redirects: bool = True,
                **kwargs: Any) -> requests.Response:
        """Make an HTTP request with error/code handling."""
        if token is not None:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers'].update({'Authorization': token})
        resp: requests.Response
        try:
            make_request = getattr(self._session, method)
            resp = make_request(self._path(path), **kwargs)
            logger.debug('Got response %s', resp)
        except requests.exceptions.SSLError as ex:
            raise SecurityException('SSL failed: %s' % ex) from ex
        except requests.exceptions.ConnectionError as ex:
            raise ConnectionFailed('Could not connect: %s' % ex) from ex

        # 200-series redirects are a common pattern on our projects, so these
        # should be supported.
        is_2xx = status.OK < resp.status_code \
            and resp.status_code < status.MULTIPLE_CHOICES
        if allow_2xx_redirects and is_2xx and 'Location' in resp.headers:
            loc = self._parse_location(resp.headers['Location'])
            logger.debug('Following 2xx redirect to %s', loc)
            resp = self.request('get', loc, token, expected_code,
                                allow_2xx_redirects)

        self._check_status(resp, expected_code)
        return resp

    def json(self, method: str, path: str, token: Optional[str] = None,
             expected_code: List[int] = [status.OK], **kwargs: Any) \
            -> Tuple[dict, int, MutableMapping]:
        """
        Perform an HTTP request to a JSON endpoint, and handle any exceptions.

        Returns
        -------
        dict
            Response content.
        int
            HTTP status code.
        dict
            Response headers.

        """
        response = self.request(method, path, token, expected_code, **kwargs)
        try:
            return response.json(), response.status_code, response.headers
        except json.decoder.JSONDecodeError as ex:
            raise BadResponse(f'Could not decode', response) from ex

    def get_status(self) -> dict:
        """Get the status of the service."""
        logger.debug('Get service status')
        content = self.json('get', 'status')[0]
        logger.debug('Got status response: %s', content)
        return content

    @classmethod
    def init_app(cls, app: Flask) -> None:
        """Set default configuration parameters for an application instance."""
        if not hasattr(cls, 'Meta'):
            raise NotImplementedError('Child class must have Meta class')
        name = cls.Meta.service_name.upper()
        app.config.setdefault(f'{name}_ENDPOINT', DEFAULT_ENDPOINT)
        app.config.setdefault(f'{name}_VERIFY', DEFAULT_VERIFY)

    @classmethod
    def get_session(cls, app: Optional[Flask] = None) -> 'HTTPIntegration':
        """Get a new session with the service."""
        if not hasattr(cls, 'Meta'):
            raise NotImplementedError('Child class must have Meta class')
        if app is None:
            app = current_app
        name = cls.Meta.service_name.upper()
        try:
            params = app.config.get_namespace(f'{name}_')
            endpoint = params.pop('endpoint')
            verify = params.pop('verify')
        except KeyError as ex:
            raise RuntimeError('Must call init_app() on app before use') from ex

        logger.debug('Create %s session at endpoint %s', name, endpoint)
        return cls(endpoint, verify=verify, **params)

    @classmethod
    def current_session(cls) -> 'HTTPIntegration':
        """Get or create an HTTP session for this context."""
        name = cls.Meta.service_name
        if not g:
            return cls.get_session()
        elif name not in g:
            setattr(g, name, cls.get_session())
        return getattr(g, name)  # type: ignore


def raise_for_http_status(status_code: int,
                          resp: Optional[requests.Response] = None) -> None:
    """
    Raise an exception based on an HTTP status code.

    Parameters
    ----------
    status_code : int
        HTTP status code.
    resp : :class:`requests.Response`
        If provided, passed to the exception.

    Raises
    ------
    :class:`RequestFailed`
        Or one of its children. See :class:`.exceptions`.

    """
    if resp is None:
        raise ValueError('No response')
    if resp.status_code >= status.INTERNAL_SERVER_ERROR:
        raise RequestFailed(f'Status: {resp.status_code}', resp)
    elif resp.status_code == status.UNAUTHORIZED:
        raise RequestUnauthorized(f'Not authorized', resp)
    elif resp.status_code == status.FORBIDDEN:
        raise RequestForbidden(f'Forbidden', resp)
    elif resp.status_code == status.NOT_FOUND:
        raise NotFound(f'No such resource: {resp.url}', resp)
    elif resp.status_code >= status.BAD_REQUEST:
        raise BadRequest(f'Bad request: {resp.content}', resp)
