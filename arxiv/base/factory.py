"""Application factory for Base app (development and testing only)."""

import logging
import os
from flask import Flask
from arxiv.base import Base, routes


def create_web_app() -> Flask:
    """Initialize and configure the base application."""
    app = Flask('base')
    basedir, _ = os.path.split(os.path.abspath(__file__))
    app.config.from_pyfile(os.path.join(basedir, 'config.py'))
    Base(app)    # Gives us access to the base UI templates and resources.
    app.register_blueprint(routes.blueprint)

    return app
