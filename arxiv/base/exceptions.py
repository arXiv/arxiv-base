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

from typing import Callable, List, Tuple

from werkzeug.exceptions import NotFound, Forbidden, Unauthorized, \
    MethodNotAllowed, RequestEntityTooLarge, BadRequest, InternalServerError, \
    HTTPException
from flask import render_template, make_response, Response

from arxiv import status

_handlers = []


class ConfigurationError(InternalServerError):
    """Raised when a configuration parameter is missing or invalid."""


def handler(exception: type) -> Callable:
    """Generate a decorator to register a handler for an exception."""
    def deco(func: Callable) -> Callable:
        """Register a function as an exception handler."""
        _handlers.append((exception, func))
        return func
    return deco


def get_handlers() -> List[Tuple[type, Callable]]:
    """
    Get a list of registered exception handlers.

    Returns
    -------
    list
        List of (:class:`.HTTPException`, callable) tuples.

    """
    return _handlers


@handler(NotFound)
def handle_not_found(error: NotFound) -> Response:
    """Render the base 404 error page."""
    rendered = render_template("base/404.html", error=error,
                               pagetitle="404 Not Found")
    response = make_response(rendered)
    response.status_code = status.HTTP_404_NOT_FOUND
    return response


@handler(Forbidden)
def handle_forbidden(error: Forbidden) -> Response:
    """Render the base 403 error page."""
    rendered = render_template("base/403.html", error=error,
                               pagetitle="403 Forbidden")
    response = make_response(rendered)
    response.status_code = status.HTTP_403_FORBIDDEN
    return response


@handler(Unauthorized)
def handle_unauthorized(error: Unauthorized) -> Response:
    """Render the base 401 error page."""
    rendered = render_template("base/401.html", error=error,
                               pagetitle="401 Unauthorized")
    response = make_response(rendered)
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return response


@handler(MethodNotAllowed)
def handle_method_not_allowed(error: MethodNotAllowed) -> Response:
    """Render the base 405 error page."""
    rendered = render_template("base/405.html", error=error,
                               pagetitle="405 Method Not Allowed")
    response = make_response(rendered)
    response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    return response


@handler(RequestEntityTooLarge)
def handle_request_entity_too_large(error: RequestEntityTooLarge) -> Response:
    """Render the base 413 error page."""
    rendered = render_template("base/413.html", error=error,
                               pagetitle="413 Request Entity Too Large")
    response = make_response(rendered)
    response.status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    return response


@handler(BadRequest)
def handle_bad_request(error: BadRequest) -> Response:
    """Render the base 400 error page."""
    rendered = render_template("base/400.html", error=error,
                               pagetitle="400 Bad Request")
    response = make_response(rendered)
    response.status_code = status.HTTP_400_BAD_REQUEST
    return response


@handler(InternalServerError)
def handle_internal_server_error(error: InternalServerError) -> Response:
    """Render the base 500 error page."""
    rendered = render_template("base/500.html", error=error,
                               pagetitle="500 Internal Server Error")
    response = make_response(rendered)
    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return response
