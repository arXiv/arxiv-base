"""Meta tools for integrations."""

import inspect
from typing import Any


class MetaIntegration(type):
    """
    Metaclass for context-bound integrations.

    The purpose of this metaclass is to simplify writing integrations that
    need to attach to the application or request context.

    A typical pattern  when using an integration's method is to first check for
    an instance of the integration on the current context, and then call the
    method on that instance. In practice, this means either performing the
    context check  every time the method is used (yuck) or implementing
    module-level functions that wrap the integration class instance methods,
    and check the context when called (also yuck).

    Here's an example of what life was like back then:


    .. code-block:: python

       class FileManagementService(object):
           '''Encapsulates a connection with the file management service.'''

           def __init__(self, *args, **kwargs) -> None:
               ...

           def get_upload_status(self, upload_id: int) -> Upload:
               ...

       def init_app(app: object = None) -> None:
           '''Set default configuration params for an application instance.'''
           config = get_application_config(app)
           config.setdefault('FILE_MANAGER_ENDPOINT', 'https://arxiv.org/')
           config.setdefault('FILE_MANAGER_VERIFY', True)

       def get_session(app: object = None) -> FileManagementService:
           '''Get a new session with the file management endpoint.'''
           config = get_application_config(app)
           endpoint = config.get('FILE_MANAGER_ENDPOINT', 'https://arxiv.org/')
           verify_cert = config.get('FILE_MANAGER_VERIFY', True)
           return FileManagementService(endpoint, verify_cert=verify_cert)

       def current_session() -> FileManagementService:
           '''Get/create :class:`.FileManagementService` for this context.'''
           g = get_application_global()
           if not g:
               return get_session()
           elif 'filemanager' not in g:
               g.filemanager = get_session()   # type: ignore
           return g.filemanager    # type: ignore

       @wraps(FileManagementService.get_upload_status)
       def get_upload_status(upload_id: int) -> Upload:
           '''See :meth:`FileManagementService.get_upload_status`.'''
           return current_session().get_upload_status(upload_id)


    and then when you want to use it:

    .. code-block:: python

       from my.cool.services import filemanager

       filemanager.get_upload_status(59192)


    A better way
    ------------
    Classes that use this metaclass are expected to implement a classmethod
    called ``current_session()`` that returns an instance of the class, similar
    to the example above. That method is responsible for getting the correct
    instance for the context.

    The net effect is that instance methods will be exposed as if they were
    class methods; behind the scenes, this metaclass will call
    ``current_session()`` and obtain the bound method from the returned
    instance.

    So you can do something like:

    .. code-block:: python

       class FileManagementService(metaclass=MetaIntegration):
           '''Encapsulates a connection with the file management service.'''

           def __init__(self, *args, **kwargs) -> None:
               ...

           def get_upload_status(self, upload_id: int) -> Upload:
               ...

           @classmethod
           def init_app(cls, app: object = None) -> None:
               '''Set default configuration params for an application instance.'''
               config = get_application_config(app)
               config.setdefault('FILE_MANAGER_ENDPOINT', 'https://arxiv.org/')
               config.setdefault('FILE_MANAGER_VERIFY', True)

           @classmethod
           def get_session(cls, app: object = None) -> 'FileManagementService':
               '''Get a new session with the file management endpoint.'''
               config = get_application_config(app)
               endpoint = config.get('FILE_MANAGER_ENDPOINT', 'https://arxiv.org/')
               verify_cert = config.get('FILE_MANAGER_VERIFY', True)
               return cls(endpoint, verify_cert=verify_cert)

           @classmethod
           def current_session(cls) -> 'FileManagementService':
               '''Get/create :class:`.FileManagementService` for this context.'''
               g = get_application_global()
               if not g:
                   return cls.get_session()
               elif 'filemanager' not in g:
                   g.filemanager = cls.get_session()   # type: ignore
               return g.filemanager    # type: ignore


    and then use it like:

    .. code-block:: python

       from my.cool.services.filemanager import FileManager

       FileManager.get_upload_status(59192)


    An even better way
    ------------------
    The example above was only a marginal improvement. What would be better
    is not having to write any of those classmethods at all.

    For an example of what that looks like, see
    :class:`.api.service.HTTPIntegration`.

    """

    def __getattribute__(self, key: str) -> Any:
        """Get the attribute from the instance bound to the current context."""
        obj = super(MetaIntegration, self).__getattribute__(key)
        if inspect.isfunction(obj):
            return getattr(self.current_session(), key)
        return obj
