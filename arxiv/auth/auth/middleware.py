"""
Middleware for interpreting authn/z information on requestsself.

This module provides :class:`AuthMiddleware`, which unpacks encrypted JSON
Web Tokens provided via the ``Authorization`` header. This is intended to
support requests that have been pre-authorized by the web server using the
authenticator service (see :mod:`authenticator`).

The configuration parameter ``JWT_SECRET`` must be set in the WSGI request
environ (e.g. Apache's SetEnv) or in the runtime environment. This must be
the same secret that was used by the authenticator service to mint the token.

To install the middleware, use the pattern described in
:mod:`arxiv.base.middleware`. For example:

.. code-block:: python

   from arxiv.base import Base
   from arxiv.base.middleware import wrap
   from arxiv.users import auth


   def create_web_app() -> Flask:
       app = Flask('foo')
       Base(app)
       auth.Auth(app)
       wrap(app, [auth.middleware.AuthMiddleware])
       return app


For convenience, this is intended to be used with
:mod:`arxiv.users.auth.decorators`.

"""

import os
from typing import Callable, Iterable, Tuple
import jwt
import logging

from werkzeug.exceptions import Unauthorized, InternalServerError

from arxiv.base.middleware import BaseMiddleware

from . import tokens
from .exceptions import InvalidToken, ConfigurationError, MissingToken
from .. import domain

logger = logging.getLogger(__name__)

WSGIRequest = Tuple[dict, Callable]


class AuthMiddleware(BaseMiddleware):
    """
    Middleware to handle auth information on requests.

    Before the request is handled by the application, the ``Authorization``
    header is parsed for an encrypted JWT. If successfully decrypted,
    information about the user and their authorization scope is attached
    to the request.

    This can be accessed in the application via
    ``flask.request.environ['session']``.  If Authorization header was not
    included, then that value will be ``None``.

    If the JWT could not be  decrypted, the value will be an
    :class:`Unauthorized` exception instance. We cannot raise the exception
    here, because the middleware is executed outside of the Flask application.
    It's up to something running inside the application (e.g.
    :func:`arxiv.users.auth.decorators.scoped`) to raise the exception.

    """

    def before(self, environ: dict, start_response: Callable) -> WSGIRequest:
        """Decode and unpack the auth token on the request."""
        environ['auth'] = None      # Create the session key, at a minimum.
        environ['token'] = None
        token = environ.get('HTTP_AUTHORIZATION')    # We may not have a token.
        if token is None:
            logger.debug('No auth token')
            return environ, start_response

        # The token secret should be set in the WSGI environ, or in os.environ.
        secret = environ.get('JWT_SECRET', os.environ.get('JWT_SECRET'))
        if secret is None:
            raise ConfigurationError('Missing decryption token')

        try:
            # Try to verify the token in the Authorization header, and attach
            # the decoded session data to the request.
            session: domain.Session = tokens.decode(token, secret)
            environ['auth'] = session

            # Attach the encrypted token so that we can use it in subrequests.
            environ['token'] = token
        except InvalidToken as e:   # Let the application decide what to do.
            logger.debug(f'Auth token not valid: {token}')
            exception = Unauthorized('Invalid auth token')
            environ['auth'] = exception
        except Exception as e:
            logger.error(f'Unhandled exception: {e}')
            exception = InternalServerError(f'Unhandled: {e}')  # type: ignore
            environ['auth'] = exception
        return environ, start_response
