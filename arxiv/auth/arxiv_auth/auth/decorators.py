"""
Scope-based authorization of user/client requests.

This module provides :func:`scoped`, a decorator factory used to protect Flask
routes for which authorization is required. This is done by specifying a
required authorization scope (see :mod:`arxiv.users.auth.scopes`) and/or by
providing a custom authorizer function.

For routes that involve specific resources, a ``resource`` callback should also
be provided. That callback function should accept the same arguments as the
route function, and return the identifier for the resource as a string.

Using :func:`scoped` with an authorizer function allows you to define
application-specific authorization logic on a per-request basis without adding
complexity to request controllers. The call signature of the authorizer
function should be: ``(session: domain.Session, *args, **kwargs) -> bool``,
where `*args` and `**kwargs` are the positional and keyword arguments,
respectively, passed by Flask to the decorated route function (e.g. the
URL parameters).

.. note:: The authorizer function is only called if the session does not have
   a global or resource-specific instance of the required scope, or if a
   required scope is not specified.

Here's an example of how you might use this in a Flask application:

.. code-block:: python

   from arxiv.users.auth.decorators import scoped
   from arxiv.users.auth import scopes
   from arxiv.users import domain


   def is_owner(session: domain.Session, user_id: str, **kwargs) -> bool:
       '''Check whether the authenticated user matches the requested user.'''
       return session.user.user_id == user_id


   def get_resource_id(user_id: str) -> str:
       '''Get the user ID from the request.'''
       return user_id


   def redirect_to_login(user_id: str) -> Response:
       '''Send the unauthorized user to the log in page.'''
       return url_for('login')


   @blueprint.route('/<string:user_id>/profile', methods=['GET'])
   @scoped(scopes.EDIT_PROFILE, resource=get_resource_id,
           authorizer=user_is_owner, unauthorized=redirect_to_login)
   def edit_profile(user_id: str):
       '''User can update their account information.'''
       data, code, headers = profile.get_profile(user_id)
       return render_template('accounts/profile.html', **data)


When the decorated route function is called...

- If no session is available from either the middleware or the legacy database,
  the ``unauthorized`` callback is called, and/or :class:`Unauthorized`
  exception is raised.
- If a required scope was provided, the session is checked for the presence of
  that scope in this order:

  - Global scope (`:*`), e.g. for administrators.
  - Resource-specific scope (`:[resource_id]`), i.e. explicitly granted for a
    particular resource.
  - Generic scope (no resource part).

- If an authorization function was provided, the function is called only if
  a required scope was not provided, or if only the generic scope was found.
- Session data is added directly to the Flask request object as
  ``request.auth``, for ease of access elsewhere in the application.
- Finally, if no exceptions have been raised, the route is called with the
  original parameters.

"""

from typing import Optional, Callable, Any, List
from functools import wraps
from flask import request
from werkzeug.exceptions import Unauthorized, Forbidden
import logging

from .. import domain

INVALID_TOKEN = {'reason': 'Invalid authorization token'}
INVALID_SCOPE = {'reason': 'Token not authorized for this action'}


logger = logging.getLogger(__name__)
logger.propagate = False


def scoped(required: Optional[domain.Scope] = None,
           resource: Optional[Callable] = None,
           authorizer: Optional[Callable] = None,
           unauthorized: Optional[Callable] = None) -> Callable:
    """
    Generate a decorator to enforce authorization requirements.

    Parameters
    ----------
    required : str
        The scope required on a user or client session in order use the
        decorated route. See :mod:`arxiv.users.auth.scopes`. If not provided,
        no scope will be enforced.
    resource : function
        If a route provides actions for a specific resource, a callable should
        be provided that accepts the route arguments and returns the resource
        identifier (str).
    authorizer : function
        In addition, an authorizer function may be passed to provide more
        specific authorization checks. For example, this function may check
        that the requesting user is the owner of a resource. Should have the
        signature: ``(session: domain.Session, *args, **kwargs) -> bool``.
        ``*args`` and ``**kwargs`` are the parameters passed to the decorated
        function. If the authorizer returns ``False``, an :class:`.`
        exception is raised.
    unauthorized : function
        DEPRECATED: Do not use this parameter. It is likely it does not do
        what you expect.
        A callback may be passed to handle cases in which the request is
        unauthorized. This function will be passed the same arguments as the
        original route function. If the callback returns anything other than
        ``None``, the return value will be treated as a response and execution
        will stop. Otherwise, an ``Unauthorized`` exception will be raised.
        If a callback is not provided (default) an ``Unauthorized`` exception
        will be raised.

    Returns
    -------
    function
        A decorator that enforces the required scope and calls the (optionally)
        provided authorizer.

    """
    if required and not isinstance(required, domain.Scope):
        required = domain.Scope(required)

    def protector(func: Callable) -> Callable:
        """Decorator that provides scope enforcement."""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Check the authorization token before executing the method.

            Will also raise exceptions passed by the auth middleware.

            Raises
            ------
            :class:`.Unauthorized`
                Raised when session data is not available.
            :class:`.`
                Raised when the session has insufficient auth scope, or the
                provided authorizer returns ``False``.

            """
            if hasattr(request, 'auth'):
                session = request.auth
            elif hasattr(request, 'session'):
                session = request.session
            else:
                raise Unauthorized('No active session on request')
            scopes: List[domain.Scope] = []
            authorized: bool = False
            logger.debug('Required: %s, authorizer: %s, unauthorized: %s',
                         required, authorizer, unauthorized)
            # Use of the decorator implies that an auth session ought to be
            # present. So we'll complain here if it's not.
            if not session or not (session.user or session.client):
                logger.debug('No valid session; aborting')
                if unauthorized is not None:
                    response = unauthorized(*args, **kwargs)
                    if response is not None:
                        return response
                raise Unauthorized('Not a valid session')

            if session.authorizations is not None:
                scopes = session.authorizations.scopes
                logger.debug('session has scopes: %s', scopes)

            # If a required scope is provided, we first check to see whether
            # the session globally or explicitly authorizes the request. We
            # then fall back to the locally-defined authorizer function if it
            # is provided.
            if required and scopes:
                # A global scope is usually granted to administrators, or
                # perhaps moderators (e.g. view submission content).
                # For example: `submission:read:*`.
                if required.as_global() in scopes:
                    logger.debug('Authorized with global scope')
                    authorized = True

                # A resource-specific scope may be granted at the auth layer.
                # For example, an admin may provide provisional access to a
                # specific resource for a specific role. This kind of
                # authorization is only supported if the service provides a
                # ``resource()`` callback to get the resource identifier.
                elif (resource is not None
                      and (
                        required.for_resource(str(resource(*args, **kwargs)))
                        in scopes)):
                    logger.debug('Authorized by specific resource')
                    authorized = True

                # If both the global and resource-specific scope authorization
                # fail, then we look for the general scope in the session.
                elif required in scopes:
                    logger.debug('Required scope is present')
                    # If an authorizer callback is provided by the service,
                    # then we will enforce whatever it returns.
                    if authorizer:
                        authorized = authorizer(session, *args, **kwargs)
                        logger.debug('Authorizer func returned %s', authorized)
                    # If no authorizer callback is provided, it is implied that
                    # the general scope is sufficient to authorize the request.
                    elif authorizer is None:
                        logger.debug('No authorizer func provided')
                        authorized = True
                # The required scope is not present. There is nothing left to
                # check.
                else:
                    logger.debug('Required scope is not present')
                    authorized = False

            elif required is None and authorizer is None:
                logger.debug('No scope required, no authorizer function;'
                             ' request is authorized.')
                authorized = True

            # If a specific scope is not required, we rely entirely on the
            # authorizer callback.
            elif authorizer is not None:
                logger.debug('Calling authorizer callback')
                authorized = authorizer(session, *args, **kwargs)
            else:
                logger.debug('No authorization path available')

            if not authorized:
                logger.debug('Session is not authorized')
                raise Forbidden('Access denied')

            logger.debug('Request is authorized, proceeding')
            return func(*args, **kwargs)
        return wrapper
    return protector
