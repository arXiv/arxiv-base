"""Application factory for Base app (development and testing only)."""

import logging
import os
from flask import Flask
from flask_s3 import FlaskS3

from arxiv.base import Base, routes

from . import config

s3 = FlaskS3()


def create_web_app() -> Flask:
    """Initialize and configure the base application."""
    app = Flask('base_test')
    # .config is an instance of a dict subclass with some methods.
    app.config.from_object(config)

    Base(app)    # Gives us access to the base UI templates and resources.
    app.register_blueprint(routes.blueprint)

    s3.init_app(app)
    return app
