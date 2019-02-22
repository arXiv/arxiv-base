"""Web Server Gateway Interface entry-point."""

import os
from typing import Mapping
from flask import Flask

from arxiv.base import Base
from arxiv import status


def create_web_app() -> Flask:
    """Create a :class:`.Flask` app."""
    app = Flask("fourohfour")
    Base(app)

    @app.route('/healthz')
    def healthz():
        """Health check endpoint."""
        return "i'm still here", status.HTTP_200_OK, {}

    return app


def application(environ, start_response):
    """WSGI application factory."""
    for key, value in environ.items():
        os.environ[key] = str(value)
    app = create_web_app()
    return app(environ, start_response)
