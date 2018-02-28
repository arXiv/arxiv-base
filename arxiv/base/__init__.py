"""arXiv base UI blueprint"""

from typing import Optional
from flask import Blueprint, Flask

from arxiv.base.context_processors import config_url_builder
from arxiv.base import exceptions


class Base(object):
    """Attaches a base UI blueprint and context processors to an app."""

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialize ``app`` with base blueprint."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Create and register the base UI blueprint."""
        # The base blueprint attaches static assets and templates.
        blueprint = Blueprint(
            'base',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=app.static_url_path + '/base'
        )
        app.register_blueprint(blueprint)

        # Register base context processors (e.g. to inject global URLs).
        app.context_processor(config_url_builder)

        # Register base exception handlers.
        for error, handler in exceptions.get_handlers():
            app.errorhandler(error)(handler)
