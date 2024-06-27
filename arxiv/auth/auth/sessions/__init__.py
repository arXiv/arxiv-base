"""
Integration with the distributed session store.

In this implementation, we use a key-value store to hold session data
in JSON format. When a session is created, a JWT cookie value is
created that contains information sufficient to retrieve the session.

See :mod:`.store`.

"""

from .store import SessionStore
