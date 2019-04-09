"""Provides base classes for WSGI middlewares."""

from typing import Callable, Union, Iterable, TypeVar, Optional, Mapping, Tuple
from typing_extensions import Protocol


WSGIRequest = Tuple[dict, Callable]
WSGIResponse = Iterable
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
    """Defines a minimal WSGI middlware factory."""

    def __call__(self, app: IWSGIApp, config: Mapping = {}) -> IWSGIMiddleware:
        """Generate a :class:`.WSGIMiddleware`."""
        ...


class BaseMiddleware:
    """
    Base class for WSGI middlewares.

    Child classes should implement one or both of:

    - ``before(environ: dict, start_response: Callable) -> Tuple[dict, Callable]``
    - ``after(response: Iterable) -> Iterable``

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
        return environ, start_response

    def after(self, response: WSGIResponse) -> WSGIResponse:
        return response

    def __call__(self, environ: dict, start: Callable) -> WSGIResponse:
        """
        Handle a WSGI request.

        Parameters
        ----------
        environ : dict
            WSGI request environment.
        start : function
            Function used to begin the HTTP response. See
            https://www.python.org/dev/peps/pep-0333/#the-start-response-callable

        Returns
        -------
        iterable
            Iterable that generates the HTTP response. See
            https://www.python.org/dev/peps/pep-0333/#the-application-framework-side

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
