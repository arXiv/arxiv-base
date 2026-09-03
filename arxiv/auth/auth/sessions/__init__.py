"""
User and client sessions.

Sessions are stateless: a session is a self-contained signed JWT cookie that
carries everything needed to verify it, so there is no external (Redis)
session store. When a session is created, a JWT cookie value is generated that
consumers verify by signature rather than by looking it up.

See :mod:`.store`.

"""

from .store import SessionStore
