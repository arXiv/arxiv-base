"""Provides base classes for WSGI middlewares."""

from typing import Callable, Union, Iterable
from flask import Flask


class BaseMiddleware(object):
    """
    Base class for WSGI middlewares.

    Child classes should reimplement :meth:`.__call__`.
    """

    def __init__(self, app: Union[Flask, Callable]):
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
        return self.app(environ, start_response)

    @property
    def wsgi_app(self):
        """
        Refer to the current instance of this class.

        This is here for consistency with the :class:`.Flask` interface.
        """
        return self
