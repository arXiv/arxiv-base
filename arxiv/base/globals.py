"""
Helpers for working with Flask globals.

Flask makes heavy use of proxy objects. Depending on the context in which code
is being executed, many of the Flask globals will refer to different things
(or sometimes nothing at all). It is nice to be able to write code without
handling the various scenarios that this creates. That's what this module is
for: instead of accessing proxies directly, the functions here will access
proxies appropriately depending on the context, and return the appropriate
object.
"""

import os
from typing import Optional, Union, Mapping
from flask import g, Flask
from flask import current_app as flask_app
import werkzeug


def get_application_config(app: Optional[Flask] = None) ->Mapping:
    """
    Get a configuration from the current app, or fall back to os.env.

    Parameters
    ----------
    app : :class:`flask.Flask`

    Returns
    -------
    dict-like
        This is either the current Flask application configuration, or
        ``os.environ``. Either of these should support the ``get()`` method.
    """
    # pylint: disable=protected-access
    if app is not None:
        if isinstance(app, Flask):
            return app.config
    if flask_app:    # Proxy object; falsey if there is no application context.
        return flask_app.config
    return os.environ


def get_application_global() -> Optional[werkzeug.local.LocalProxy]:
    """
    Get the current application global proxy object.

    Returns
    -------
    proxy or None
    """
    if g:
        return g    # type: ignore
    return None
