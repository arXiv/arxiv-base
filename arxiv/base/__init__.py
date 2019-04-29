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
import types
from typing import Optional, Any, Dict
from flask import Blueprint, Flask, Blueprint
from werkzeug.exceptions import NotFound

from . import exceptions, urls, alerts, context_processors, filters
from . import config as base_config
from .converter import ArXivConverter


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

        # Set the static url path.
        app_version = app.config.get("APP_VERSION", "null")
        app_static_path = f'/static/{app.name}/{app_version}'
        app.static_url_path = app_static_path

        # We also need to update the app's url_map, since that's how url_for()
        # builds URLs.
        # Remove the rule from the url_map.
        for rule in app.url_map.iter_rules('static'):
            app.url_map._rules.remove(rule)
        # Werkzeug maintains this for faster lookup; we need to clear it, too.
        app.url_map._rules_by_endpoint['static'] = []
        # Add the updated rule.
        app.add_url_rule(f'{app.static_url_path}/<path:filename>',
                         endpoint='static',
                         view_func=app.send_static_file)

        base_static_url_path = f'/static/base/{base_config.BASE_VERSION}'

        # In some cases, we want an app to handle all of its static files, e.g.
        # when deploying in a development environment. Setting the
        # configuration param RELATIVE_STATIC_PATHS to True will cause
        # ``/{RELATIVE_STATIC_PATHS}`` to be prepended to the static paths for
        # base assets. This should have no impact on static paths for
        # blueprints.
        if app.config.get('RELATIVE_STATIC_PATHS'):
            prefix = app.config.get('RELATIVE_STATIC_PREFIX', '').strip('/')
            base_static_url_path = f'/{prefix}{base_static_url_path}'

        # The base blueprint attaches static assets and templates. These are
        # used by many different apps.
        #
        # We include the version of this package in the static path, so that
        # apps can run slightly different versions of this package without
        # clobbering each other.
        blueprint = Blueprint(
            'base',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=base_static_url_path
        )
        app.register_blueprint(blueprint)

        # 2019-01-31 - Erick P.:
        #
        # We need to able able to set the static URL for blueprints, so that
        # we can ensure a consistent URL strategy. Changing the static URL for
        # a blueprint after it is registered won't work, because the blueprint
        # will have already set up its internal machinery via
        # Blueprint.register(), which is called by Flask.register_blueprint().
        # In order to intercept and modify the blueprint before
        # Blueprint.register() is called, we swap out the app's
        # register_blueprint() method for a closure (below) that alters the
        # static URL path.
        def register_blueprint(self: Flask, blueprint: Blueprint,
                               **options: Any) -> None:
            blueprint.static_url_path = f'{app_static_path}/{blueprint.name}'
            self._register_blueprint(blueprint, **options)

        app._register_blueprint = app.register_blueprint
        app.register_blueprint = types.MethodType(register_blueprint, app)    # type: ignore

        # Register base exception handlers.
        for error, handler in exceptions.get_handlers():
            app.errorhandler(error)(handler)

        # Attach the external URL handler as a fallback for failed calls to
        # url_for().
        urls.register_external_urls(app)

        filters.register_filters(app)
        context_processors.register_context_processors(app)
