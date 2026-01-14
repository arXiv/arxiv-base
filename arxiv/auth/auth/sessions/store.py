"""
Internal service API for the distributed session store.

Used to create, delete, and verify user and client session.
"""

import uuid
import random
from datetime import datetime, timedelta
import dateutil.parser
from pytz import timezone, UTC
import logging

from typing import Optional, Union

import redis
import rediscluster

import jwt

from .. import domain
from ..exceptions import (
    SessionCreationFailed,
    InvalidToken,
    SessionDeletionFailed,
    UnknownSession,
    ExpiredToken,
)

from arxiv.base.globals import get_application_config, get_application_global

logger = logging.getLogger(__name__)
EASTERN = timezone("US/Eastern")


def _generate_nonce(length: int = 8) -> str:
    return "".join([str(random.randint(0, 9)) for i in range(length)])


class SessionStore(object):
    """
    Manages a connection to Redis.

    In fact, the StrictRedis instance is thread safe and connections are
    attached at the time a command is executed. This class simply provides a
    container for configuration.

    Pass fake=True to use FakeRedis for testing of development.
    """

    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        secret: str,
        duration: int = 7200,
        token: Optional[str] = None,
        cluster: bool = True,
        fake: bool = False,
    ) -> None:
        """Open the connection to Redis."""
        self._secret = secret
        self._duration = duration
        if fake:
            logger.warning("Using FakeRedis")
            import fakeredis  # this is a dev dependency needed during testing

            self.r = fakeredis.FakeStrictRedis()
        else:
            logger.debug("New Redis connection at %s, port %s", host, port)
            if cluster:
                self.r = rediscluster.StrictRedisCluster(
                    startup_nodes=[{"host": host, "port": str(port)}],
                    skip_full_coverage_check=True,
                )
            else:
                self.r = redis.StrictRedis(host=host, port=port)

    def create(
        self,
        authorizations: domain.Authorizations,
        ip_address: str,
        remote_host: str,
        tracking_cookie: str = "",
        user: Optional[domain.User] = None,
        client: Optional[domain.Client] = None,
        session_id: Optional[str] = None,
    ) -> domain.Session:
        """
        Create a new session.

        Parameters
        ----------
        authorizations : :class:`domain.Authorizations`
        ip_address : str
        remote_host : str
        tracking_cookie : str
        user : :class:`domain.User`
        client : :class:`domain.Client`

        Returns
        -------
        :class:`.Session`

        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        start_time = datetime.now(tz=UTC)
        end_time = start_time + timedelta(seconds=self._duration)
        session = domain.Session(
            session_id=session_id,
            user=user,
            client=client,
            start_time=start_time,
            end_time=end_time,
            authorizations=authorizations,
            nonce=_generate_nonce(),
        )
        logger.debug("storing session %s", session)
        try:
            self.r.set(
                session_id,
                jwt.encode(session.json_safe_dict(), self._secret),
                ex=self._duration,
            )
        except redis.exceptions.ConnectionError as e:
            raise SessionCreationFailed(f"Connection failed: {e}") from e
        except Exception as e:
            raise SessionCreationFailed(f"Failed to create: {e}") from e

        return session

    def generate_cookie(self, session: domain.Session) -> str:
        """Generate a cookie from a :class:`domain.Session`."""
        if session.end_time is None:
            raise RuntimeError("Session has no expiry")
        if session.user is None:
            raise RuntimeError("Session user is not set")
        return self._pack_cookie(
            {
                "user_id": session.user.user_id,
                "session_id": session.session_id,
                "nonce": session.nonce,
                "expires": session.end_time.isoformat(),
            }
        )

    def delete(self, cookie: str) -> None:
        """
        Delete a session.

        Parameters
        ----------
        cookie : str

        """
        cookie_data = self._unpack_cookie(cookie)
        self.delete_by_id(cookie_data["session_id"])

    def delete_by_id(self, session_id: str) -> None:
        """
        Delete a session in the key-value store by ID.

        Parameters
        ----------
        session_id : str

        """
        try:
            self.r.delete(session_id)
        except redis.exceptions.ConnectionError as e:
            raise SessionDeletionFailed(f"Connection failed: {e}") from e
        except Exception as e:
            raise SessionDeletionFailed(f"Failed to delete: {e}") from e

    def validate_session_against_cookie(
        self, session: domain.Session, cookie: str
    ) -> None:
        """
        Validate session data against a cookie.

        Parameters
        ----------
        session : :class:`Session`
        cookie : str

        Raises
        ------
        :class:`InvalidToken`
            Raised if the data in the cookie does not match the session data.

        """
        cookie_data = self._unpack_cookie(cookie)
        if (
            cookie_data["nonce"] != session.nonce
            or session.user is None
            or session.user.user_id != cookie_data["user_id"]
        ):
            raise InvalidToken("Invalid token; likely a forgery")

    def load(
        self, cookie: str, decode: bool = True
    ) -> Union[domain.Session, str, bytes]:
        """Load a session using a session cookie."""
        try:
            cookie_data = self._unpack_cookie(cookie)
            expires = dateutil.parser.parse(cookie_data["expires"])
        except (KeyError, jwt.exceptions.DecodeError) as e:
            raise InvalidToken("Token payload malformed") from e

        if expires <= datetime.now(tz=UTC):
            raise InvalidToken("Session has expired")

        session = self.load_by_id(cookie_data["session_id"], decode=decode)

        if not decode:
            assert isinstance(session, str) or isinstance(session, bytes)
            return session
        assert isinstance(session, domain.Session)
        if session.expired:
            raise ExpiredToken("Session has expired")
        if session.user is None and session.client is None:
            raise InvalidToken("Neither user nor client data are present")

        self.validate_session_against_cookie(session, cookie)
        return session

    def load_by_id(
        self, session_id: str, decode: bool = True
    ) -> Union[domain.Session, str, bytes]:
        """Get session data by session ID."""
        session_jwt: str = self.r.get(session_id)
        if not session_jwt:
            logger.debug(f"No such session: {session_id}")
            raise UnknownSession(f"Failed to find session {session_id}")
        if decode:
            return self._decode(session_jwt)
        return session_jwt

    def _encode(self, session_data: dict) -> bytes:
        return jwt.encode(session_data, self._secret)

    def _decode(self, session_jwt: str) -> domain.Session:
        try:
            return domain.Session.parse_obj(
                jwt.decode(session_jwt, self._secret, algorithms=["HS256"])
            )
        except jwt.exceptions.InvalidSignatureError:
            raise InvalidToken("Invalid or corrupted session token")

    def _unpack_cookie(self, cookie: str) -> dict:
        secret = self._secret
        try:
            data = dict(jwt.decode(cookie, secret, algorithms=["HS256"]))
        except jwt.exceptions.DecodeError as e:
            raise InvalidToken("Session cookie is malformed") from e
        return data

    def _pack_cookie(self, cookie_data: dict) -> str:
        secret = self._secret
        return jwt.encode(cookie_data, secret)

    @classmethod
    def init_app(cls, app: object = None) -> None:
        """Set default configuration parameters for an application instance."""
        config = get_application_config(app)
        config.setdefault("REDIS_HOST", "localhost")
        config.setdefault("REDIS_PORT", "7000")
        config.setdefault("REDIS_DATABASE", "0")
        config.setdefault("REDIS_TOKEN", None)
        config.setdefault("REDIS_CLUSTER", "1")
        config.setdefault("JWT_SECRET", "foosecret")
        config.setdefault("SESSION_DURATION", "7200")
        config.setdefault("REDIS_FAKE", False)

    @classmethod
    def get_session(cls, app: object = None) -> "SessionStore":
        """Get a new session with the search index."""
        config = get_application_config(app)
        host = config.get("REDIS_HOST", "localhost")
        port = int(config.get("REDIS_PORT", "7000"))
        db = int(config.get("REDIS_DATABASE", "0"))
        token = config.get("REDIS_TOKEN", None)
        cluster = config.get("REDIS_CLUSTER", "1") == "1"
        secret = config["JWT_SECRET"]
        duration = int(config.get("SESSION_DURATION", "7200"))
        fake = config.get("REDIS_FAKE", False)
        return cls(
            host, port, db, secret, duration, token=token, cluster=cluster, fake=fake
        )

    @classmethod
    def current_session(cls) -> "SessionStore":
        """Get/create :class:`.SearchSession` for this context."""
        g = get_application_global()
        if not g:
            return cls.get_session()
        if "redis" not in g:
            g.redis = cls.get_session()
        return g.redis  # type: ignore
