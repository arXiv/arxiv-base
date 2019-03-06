"""Meta tools for integrations."""

import inspect


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
    and check the context  when called (also yuck).

    Classes that use this metaclass are expected to implement a classmethod
    called ``current_session()`` that returns an instance of the class. That
    method is responsible for getting the correct instance for the context.

    The net effect is that instance methods will be exposed as if they were
    class methods; behind the scenes, this metaclass will call
    ``current_session()`` and obtain the bound method from the returned
    instance.
    """

    def __getattribute__(self, key):
        """Get the attribute from the instance bound to the current context."""
        obj = super(MetaIntegration, self).__getattribute__(key)
        if inspect.isfunction(obj):
            return getattr(self.current_session(), key)
        return obj
