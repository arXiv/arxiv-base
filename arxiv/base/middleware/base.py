"""Provides base classes for WSGI middlewares."""

from typing import Callable, Union, Iterable, TypeVar
from flask import Flask


class BaseMiddleware(object):
    """
    Base class for WSGI middlewares.

    Child classes should implement one or both of:

    - ``before(environ: dict, start_response: Callable) -> Tuple[dict, Callable]``
    - ``after(response: Iterable) -> Iterable``

    """

    def __init__(self, app: Union[Flask, Callable]) -> None:
        """
        Set the app factory that this middleware wraps.

        Parameters
        ----------
        app : :class:`.Flask` or callable
            The application wrapped by this middleware. This might be an inner
            middleware, or the original :class:`.Flask` app itself.

        """
        self.app = app

    def __call__(self, environ: dict, start_response: Callable) -> Iterable:
        """
        Handle a WSGI request.

        Parameters
        ----------
        environ : dict
            WSGI request environment.
        start_response : function
            Function used to begin the HTTP response. See
            https://www.python.org/dev/peps/pep-0333/#the-start-response-callable

        Returns
        -------
        iterable
            Iterable that generates the HTTP response. See
            https://www.python.org/dev/peps/pep-0333/#the-application-framework-side
        """
        if hasattr(self, 'before'):
            environ, start_response = self.before(environ, start_response)  # type: ignore
        response: Iterable = self.app(environ, start_response)

        if hasattr(self, 'after'):
            response = self.after(response)       # type: ignore
        return response

    @property
    def wsgi_app(self):    # type: ignore
        """
        Refer to the current instance of this class.

        This is here for consistency with the :class:`.Flask` interface.
        """
        return self
