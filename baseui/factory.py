"""Application factory for BaseUI app (development and testing only)."""

import logging

from flask import Flask
from baseui import BaseUI, routes


def create_web_app() -> Flask:
    """Initialize and configure the zero application."""
    app = Flask('baseui')
    app.config.from_pyfile('config.py')
    BaseUI(app)    # Gives us access to the base UI templates and resources.
    app.register_blueprint(routes.blueprint)
    return app
