"""Application factory for BaseUI app (development and testing only)."""

import logging

from flask import Flask
from arxiv.base import Base, routes


def create_web_app() -> Flask:
    """Initialize and configure the zero application."""
    app = Flask('base')
    app.config.from_pyfile('config.py')
    Base(app)    # Gives us access to the base UI templates and resources.
    app.register_blueprint(routes.blueprint)
    return app
