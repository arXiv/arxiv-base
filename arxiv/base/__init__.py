"""
arXiv base Flask components.

Provides :class:`.Base`, which attaches base templates, static assets, global
context processors, and exception handlers to a :class:`flask.Flask` app
instance.

Intended for use in an application factory. For example:

.. code-block:: python

   python
   from flask import Flask
   from arxiv.base import Base
   from someapp import routes


   def create_web_app() -> Flask:
      app = Flask('someapp')
      app.config.from_pyfile('config.py')

      Base(app)   # Registers the base/UI blueprint.
      app.register_blueprint(routes.blueprint)    # Your blueprint.
   return app


"""

from typing import Optional
from flask import Blueprint, Flask
from werkzeug.exceptions import NotFound

from arxiv.base.context_processors import config_url_builder
from arxiv.base import exceptions, urls, config
from arxiv.base.converter import ArXivConverter


def placeholder(*args, **kwargs):
    """Placeholder route for external endpoints."""
    raise NotFound("This endpoint is not provided by this service.")


class Base(object):
    """Attaches a base UI blueprint and context processors to an app."""

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialize ``app`` with base blueprint."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Create and register the base UI blueprint."""
        # Attach the arXiv identifier converter for URLs with IDs.
        app.url_map.converters['arxiv'] = ArXivConverter

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

        # Register URLs for other services. This allows us to use flask's
        # ``url_for()`` function to generate URLs for services that are
        # deployed at the same hostname.
        for name, pattern in config.ARXIV_URLS:
            app.add_url_rule(pattern, name, placeholder)
