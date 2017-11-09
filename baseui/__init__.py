from flask import Blueprint


class BaseUI(object):
    """Attaches a base UI blueprint to an application."""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Creates and registers the base UI blueprint."""
        blueprint = Blueprint(
            'baseui',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=app.static_url_path + '/base',)
        app.register_blueprint(blueprint)
