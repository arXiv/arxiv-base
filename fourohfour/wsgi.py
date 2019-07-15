"""Web Server Gateway Interface entry-point."""

import os
from typing import Mapping
from flask import Flask

from arxiv.base import Base
from http import HTTPStatus as status


def create_web_app() -> Flask:
    """Create a :class:`.Flask` app."""
    app = Flask("fourohfour")
    Base(app)

    @app.route('/healthz')
    def healthz():
        """Health check endpoint."""
        return "i'm still here", status.OK, {}

    return app


__flask_app__ = create_web_app()


def application(environ, start_response):
    """WSGI application factory."""
    for key, value in environ.items():
        if key == 'SERVER_NAME':    # This will only confuse Flask.
            continue
        os.environ[key] = str(value)
        __flask_app__.config[key] = value
    return __flask_app__(environ, start_response)
