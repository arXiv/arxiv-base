"""Provides a base class for HTTP service integrations."""

from typing import Optional, Tuple, MutableMapping, List
import inspect
import requests
from urllib3.util.retry import Retry
from urllib.parse import urlparse, urlunparse, urlencode
import json

from flask import g, Flask, current_app

from . import status
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
    """

    class Meta:
        """
        Additional info about this class.

        This should be overridden by any child class.
        """

        service_name = "base"

    def __init__(self, endpoint: str, verify: bool = True,
                 headers: dict = {}) -> None:
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

        """
        self._session = requests.Session()
        self._verify = verify
        self._retry = Retry(  # type: ignore
            total=10,
            read=10,
            connect=10,
            status=10,
            backoff_factor=0.5
        )
        self._adapter = requests.adapters.HTTPAdapter(max_retries=self._retry)
        self._session.mount(f'{urlparse(endpoint).scheme}://', self._adapter)
        if not endpoint.endswith('/'):
            endpoint += '/'
        self._endpoint = endpoint
        self._session.headers.update(headers)

    def _path(self, path: str, query: dict = {}) -> str:
        """Generate a full path for a request."""
        o = urlparse(self._endpoint)
        path = path.lstrip('/')
        return urlunparse((  # type: ignore
            o.scheme, o.netloc, f"{o.path}{path}",
            None, urlencode(query), None
        ))

    def _check_status(self, resp: requests.Response,
                      expected_code: List[int] = [status.HTTP_200_OK]) -> None:
        """Check for unexpected or errant status codes."""
        if resp.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise RequestFailed(f'Status: {resp.status_code}', resp)
        elif resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise RequestUnauthorized(f'Not authorized', resp)
        elif resp.status_code == status.HTTP_403_FORBIDDEN:
            raise RequestForbidden(f'Forbidden', resp)
        elif resp.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFound(f'No such resource: {resp.url}', resp)
        elif resp.status_code >= status.HTTP_400_BAD_REQUEST:
            raise BadRequest(f'Bad request: {resp.content}', resp)
        elif resp.status_code not in expected_code:
            raise RequestFailed(f'Unexpected code: {resp.status_code}', resp)

    def request(self, method: str, path: str, token: Optional[str] = None,
                expected_code: List[int] = [status.HTTP_200_OK], **kwargs) \
            -> requests.Response:
        """Make an HTTP request with error/code handling."""
        if token is not None:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers'].update({'Authorization': token})
        try:
            resp = getattr(self._session, method)(self._path(path), **kwargs)
            logger.debug('Got response %s', resp)
        except requests.exceptions.SSLError as e:
            raise SecurityException('SSL failed: %s' % e) from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailed('Could not connect: %s' % e) from e
        self._check_status(resp, expected_code)
        return resp

    def json(self, method: str, path: str, token: Optional[str] = None,
             expected_code: List[int] = [status.HTTP_200_OK], **kwargs) \
            -> Tuple[dict, MutableMapping]:
        """
        Perform an HTTP request to a JSON endpoint, and handle any exceptions.

        Returns
        -------
        dict
            Response content.
        dict
            Response headers.

        """
        resp = self.request(method, path, token, expected_code, **kwargs)
        try:
            return resp.json(), resp.headers
        except json.decoder.JSONDecodeError as e:
            raise BadResponse(f'Could not decode', resp) from e

    def get_status(self) -> dict:
        """Get the status of the file management service."""
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
            endpoint = app.config[f'{name}_ENDPOINT']
            verify = app.config[f'{name}_VERIFY']
        except KeyError as e:
            raise RuntimeError('Must call init_app() on app before use') from e
        logger.debug('Create %s session at endpoint %s', name, endpoint)
        return cls(endpoint, verify=verify)

    @classmethod
    def current_session(cls) -> 'HTTPIntegration':
        """Get or create an HTTP session for this context."""
        name = cls.Meta.service_name
        if not g:
            return cls.get_session()
        elif name not in g:
            setattr(g, name, cls.get_session())  # type: ignore
        return getattr(g, name)  # type: ignore
