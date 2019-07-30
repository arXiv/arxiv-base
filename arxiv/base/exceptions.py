"""
Provides base HTTP exceptions and exception handling.

arXiv-base exceptions inherit from `Werkzeug HTTPExceptions
<http://werkzeug.pocoo.org/docs/0.14/exceptions/>`_. In most cases it will
make sense to simply use Werkzeug's many HTTP exceptions directly. Custom
exceptions can also be defined by further subclassing those exceptions.

These handlers are attached to any Flask app passed to
:class:`arxiv.base.Base`. Thus any services that extends arXiv base need only
define (if needed) and raise exceptions.

Controllers should raise HTTP exceptions. The exception message (description)
will be rendered within the base template for that exception class, including
markup.
"""

from typing import Callable, List, Tuple, Type, Dict

from werkzeug.exceptions import NotFound, Forbidden, Unauthorized, \
    MethodNotAllowed, RequestEntityTooLarge, BadRequest, InternalServerError, \
    HTTPException, default_exceptions
from flask import render_template, make_response, Response, request

from http import HTTPStatus as status

_handlers: List[Tuple[Type[HTTPException],
                      Callable[[HTTPException], Response]]] = []


class ConfigurationError(InternalServerError):
    """Raised when a configuration parameter is missing or invalid."""


def handler(exception_type: Type[HTTPException]) -> Callable:
    """Generate a decorator to register a handler for an exception."""
    def deco(func: Callable) -> Callable:
        """Register a function as an exception handler."""
        _handlers.append((exception_type, func))
        return func
    return deco


def get_handlers() -> List[Tuple[Type[HTTPException], Callable]]:
    """
    Get a list of registered exception handlers.

    Returns
    -------
    list
        List of (:class:`.HTTPException`, callable) tuples.

    """
    return _handlers


def handle_exception(error: HTTPException) -> Response:
    """Render a generic error handler."""
    rendered = render_template("base/exception.html", error=error,
                               pagetitle=f"{error.code} {error.name }")
    response: Response = make_response(rendered, error.code)
    return response


# Generate handlers programmatically from the built-in Werkzeug HTTP
# exceptions.
for code, exception_type in default_exceptions.items():
    handler(exception_type)(handle_exception)