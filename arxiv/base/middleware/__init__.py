r"""
WSGI middleware integration for Flask apps.

A WSGI middleware sits "between" the WSGI server (e.g. uWSGI) and the Flask
application. This allows us to execute code on each request, either before or
after the request is handled by Flask application. For example, a middleware
could be used to parse and validate authorization information before a request
is handled. In practical terms, a middleware is a wrapper around a Flask
application instance.

Writing a middleware
====================

Middlewares may subclass :class:`.base.BaseMiddleware`, which implements some
of the boilerplate needed to make the middleware work with Flask. In that case,
the middleware class need only implement one or both of:

- ``before(environ: dict, start_response: Callable) -> Tuple[dict, Callable]``
- ``after(response: Iterable) -> Iterable``

For example:

.. code-block:: python

   from arxiv.base.middleware import BaseMiddleware

   class FooMiddleware(BaseMiddleware):
       '''Adds the parameter ``foo`` to the request environment.'''

       def before(self, environ: dict, start_response: Callable) \
               -> Tuple[dict, Callable]:
           '''Insert ``foo`` into the environment, and handle the request.'''
           environ['foo'] = 'bar'
           return environ, start_response


In the example above, the ``'foo'`` parameter would be available on the
:prop:`.Flask.request.environ` object within the Flask application.

.. code-block:: python

   from flask import request

   @app.route('/')
   def my_route():
       foo = request.environ['foo']
       return f'The value of foo is {foo}'

For more information, see the `WSGI spec
<https://www.python.org/dev/peps/pep-0333/>`_.

Adding a middleware to a project
================================
This module provides a function called :func:`.wrap` that applies a list of
middlewares to a :class:`.Flask` application. This works by instantiating a
middleware class with a reference to the Flask app, and then replacing the
app's ``wsgi_app`` property with the middleware. In this sense, the middleware
wraps the Flask application.

:func:`.wrap` applies middlewares in reverse order, which means that the
first middleware will be the "outermost" middleware, and will therefore be
called first upon each request.

.. code-block:: python

   from arxiv.base.middleware import wrap
   app = Flask('some_app')
   wrap(app, [FirstMiddleware, SecondMiddleware, ThirdMiddleware])



"""

from typing import Type, Callable, List, Union
from flask import Flask

from .base import BaseMiddleware, IWSGIMiddlewareFactory, IWSGIApp


def wrap(app: Flask, middlewares: List[IWSGIMiddlewareFactory]) -> Callable:
    """
    Wrap a :class:`.Flask` app in WSGI middlewares.

    Parameters
    ----------
    app : :class:`.Flask`
        The Flask app to wrap.
    middlewares : list
        A list of middleware classes. These are applied in reverse, so that the
        first middleware is the "outermost" wrapper around the base ``app``,
        and is therefore called first.

    Returns
    -------
    :class:`.Flask`
        The original Flask ``app``, with middlewares applied.

    """
    if not hasattr(app, 'wsgi_app'):
        raise TypeError('Not a valid Flask app or middleware')
    # Apply the last middleware first, so that the first middleware is called
    # first upon the request.
    wrapped_app: IWSGIApp = app.wsgi_app
    for middleware in middlewares[::-1]:
        try:
            wrapped_app = middleware(wrapped_app, config=app.config)
        except TypeError:   # Maintain backward compatibility.
            wrapped_app = middleware(wrapped_app)
    app.wsgi_app = wrapped_app  # type: ignore
    return app
