"""
Web Server Gateway Interface entry-point."""

import os
from http import HTTPStatus as status
from typing import Mapping

from flask import Flask, Response, make_response, request, jsonify
from werkzeug.exceptions import default_exceptions, NotFound, HTTPException

from arxiv.base import Base, exceptions


def make_error_response() -> None:
    """Raise an :class:`.HTTPException` based on the status in ``X-Code``."""
    data = {'request_id': request.headers['X-Request-ID']}
    code = int(request.headers['X-Code'])
    exception = default_exceptions[code]
    raise exception(data)


def content_aware_exception_handler(error: HTTPException) -> Response:
    """
    Error handler with support for the ``X-Format`` header.

    Looks to ``X-Format`` for the content type originally requested by the
    client (e.g. via ``Accept`` request header).

    Falls back to the base exception handler.
    """
    if request.headers.get('X-Format') == 'application/json':
        data = {'error': error.code, 'name': error.name,
                'detail': error.description}
        return make_response(jsonify(data), error.code)
    return exceptions.handle_exception(error)


def echo() -> None:
    """Propagate an exception from NGINX."""
    try:
        make_error_response()
    except KeyError:    # Fall back to a 404 if error info is not available.
        raise NotFound('Nope')


def healthz() -> Response:
    """Health check endpoint."""
    response: Response = make_response("i'm still here", status.OK)
    return response


def create_web_app() -> Flask:
    """Create a :class:`.Flask` app."""
    app = Flask("fourohfour")
    Base(app)

    # Override the default error handlers to provide content negotation.
    for _, error in default_exceptions.items():
        app.errorhandler(error)(content_aware_exception_handler)

    app.route('/healthz')(healthz)
    app.route('/')(echo)
    return app


__flask_app__ = create_web_app()
app = __flask_app__


def application(environ, start_response):
    """WSGI application factory."""
    for key, value in environ.items():
        if key == 'SERVER_NAME':
            continue
        os.environ[key] = str(value)
        if key in __flask_app__.config:
            __flask_app__.config[key] = value

    return app(environ, start_response)
