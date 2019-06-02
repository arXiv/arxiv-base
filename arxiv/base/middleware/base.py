"""Provides base classes for WSGI middlewares."""

from typing import Callable, Union, Iterable, TypeVar, Optional, Mapping, Tuple
from typing_extensions import Protocol


WSGIRequest = Tuple[dict, Callable]
"""
The WSGI request.

Comprised of an environ mapping and a callable for starting the response. See
also `https://www.python.org/dev/peps/pep-0333/#the-start-response-callable`_.
"""

WSGIResponse = Iterable
"""
The iterable that generates a WSGI response.

See also
`https://www.python.org/dev/peps/pep-0333/#the-application-framework-side`_.
"""

IWSGIApp = Callable[[dict, Callable], WSGIResponse]


class IWSGIMiddleware(Protocol):
    """Defines a minimal class that can be used as a middleware."""

    def __init__(self, wsgi_app: IWSGIApp, config: Mapping = {}) -> None:
        """Initialize with an WSGI app and an optional configuration."""
        ...

    def __call__(self, environ: dict, start: Callable) -> WSGIResponse:
        """Support the WSGI protocol."""
        ...

    @property
    def wsgi_app(self) -> IWSGIApp:
        """Offer a ``wsgi_app`` property, per :class:`.Flask` behavior."""
        ...


class IWSGIMiddlewareFactory(Protocol):
    """Defines a minimal WSGI middleware factory."""

    def __call__(self, app: IWSGIApp, config: Mapping = {}) -> IWSGIMiddleware:
        """Generate a :class:`.WSGIMiddleware`."""
        ...


class BaseMiddleware:
    r"""
    Base class for WSGI middlewares.

    Child classes should override :func:`.before` and/or :func:`.after`\.
    """

    def __init__(self, wsgi_app: IWSGIApp, config: Mapping = {}) -> None:
        """
        Set the app factory that this middleware wraps.

        Parameters
        ----------
        wsgi_app : callable
            The application wrapped by this middleware. This might be an inner
            middleware, or the original :class:`.Flask` app itself.
        config : dict
            Application configuration.

        """
        self.app = wsgi_app
        self.config = config

    def before(self, environ: dict, start_response: Callable) -> WSGIRequest:
        """
        Pre-process a WSGI request. To be overridden by a child class.

        Parameters
        ----------
        environ : dict
            WSGI request environ.
        start : callable
            Callable used to begin the HTTP response.

        Returns
        -------
        dict
            WSGI request environ.
        callable
            Callable used to begin the HTTP response.

        """
        return environ, start_response

    def after(self, response: WSGIResponse) -> WSGIResponse:
        """
        Post-process a WSGI response. To be overridden by a child class.

        Parameters
        ----------
        response : iterable
            The WSGI response.

        Returns
        -------
        iterable
            The WSGI response.

        """
        return response

    def __call__(self, environ: dict, start: Callable) -> WSGIResponse:
        r"""
        Handle a WSGI request.

        Parameters
        ----------
        environ : dict
            WSGI request environment.
        start : function
            Function used to begin the HTTP response. See
            :const:`.WSGIRequest`\.

        Returns
        -------
        iterable
            Iterable that generates the HTTP response. See
            :const:`.WSGIResponse`\.

        """
        environ, start_response = self.before(environ, start)
        response: WSGIResponse = self.app(environ, start)
        response = self.after(response)
        return response

    @property
    def wsgi_app(self) -> IWSGIApp:
        """
        Refer to the current instance of this class.

        This is here for consistency with the :class:`.Flask` interface.
        """
        return self
