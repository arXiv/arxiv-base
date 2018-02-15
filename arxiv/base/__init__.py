"""arXiv base UI blueprint"""

from typing import Optional
from flask import Blueprint, Flask

from .context_processors import config_url_builder


class Base(object):
    """Attaches a base UI blueprint and context processors to an app."""

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialize ``app`` with base blueprint."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Create and register the base UI blueprint."""
        blueprint = Blueprint(
            'base',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=app.static_url_path + '/base',)
        app.register_blueprint(blueprint)
        app.context_processor(config_url_builder)
