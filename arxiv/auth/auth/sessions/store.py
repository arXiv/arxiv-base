"""
Internal service API for user and client sessions.

Used to create, delete, and verify user and client sessions.

Sessions are no longer held in a distributed (Redis) store. A session is a
self-contained signed JWT cookie: everything needed to verify it travels in the
cookie itself. :class:`SessionStore` keeps its historical interface so existing
callers continue to work, but performs no external storage -- the methods that
used to read from or write to Redis are now stateless (see each method).
"""

import uuid
import random
from datetime import datetime, timedelta
import dateutil.parser
from pytz import timezone, UTC
import logging

from typing import Optional, Union

import jwt

from .. import domain
from ..exceptions import InvalidToken, UnknownSession, ExpiredToken

from arxiv.base.globals import get_application_config, get_application_global

logger = logging.getLogger(__name__)
EASTERN = timezone('US/Eastern')


def _generate_nonce(length: int = 8) -> str:
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def pack_cookie(session: domain.Session, secret: str) -> str:
    """Generate the `ARXIVNG_SESSION_ID` cookie value for a session.

    The cookie is a self-contained signed JWT. Consumers verify its signature
    rather than looking the session up in a store, so this needs no connection
    and can be used for sessions that live only in the legacy DB.
    """
    if session.end_time is None:
        raise RuntimeError('Session has no expiry')
    if session.user is None:
        raise RuntimeError('Session user is not set')
    if session.nonce is None:
        # A null nonce fails validation in consumers that model it as a
        # required str, so refuse to mint a cookie that cannot be used.
        raise RuntimeError('Session nonce is not set')
    return jwt.encode({
        'user_id': session.user.user_id,
        'session_id': session.session_id,
        'nonce': session.nonce,
        'expires': session.end_time.isoformat()
    }, secret)


class SessionStore(object):
    """
    Manages user and client sessions.

    Historically this managed a connection to Redis. Sessions are now stateless
    self-contained JWT cookies, so this class holds no connection; it only
    carries the signing secret and the session duration. The Redis-specific
    constructor arguments are accepted and ignored for source compatibility.
    """

    def __init__(self, host: str, port: int, db: int, secret: str,
                 duration: int = 7200, token: Optional[str] = None,
                 cluster: bool = True, fake: bool = False) -> None:
        """Configure the (stateless) session store.

        ``host``, ``port``, ``db``, ``token``, ``cluster`` and ``fake`` are
        legacy Redis parameters, retained in the signature for compatibility
        but ignored -- no connection is opened.
        """
        self._secret = secret
        self._duration = duration

    def create(self, authorizations: domain.Authorizations,
               ip_address: str, remote_host: str, tracking_cookie: str = '',
               user: Optional[domain.User] = None,
               client: Optional[domain.Client] = None,
               session_id: Optional[str] = None) -> domain.Session:
        """
        Create a new session.

        The session is returned but not persisted anywhere; its cookie (see
        :meth:`generate_cookie`) is self-contained.

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
            nonce=_generate_nonce()
        )
        logger.debug('created session %s', session)
        return session

    def generate_cookie(self, session: domain.Session) -> str:
        """Generate a cookie from a :class:`domain.Session`."""
        return pack_cookie(session, self._secret)

    def delete(self, cookie: str) -> None:
        """
        Delete a session.

        Sessions are stateless, so there is nothing to remove server-side;
        clearing the cookie ends the session. Retained as a no-op so callers do
        not need to change.

        Parameters
        ----------
        cookie : str

        """
        return None

    def delete_by_id(self, session_id: str) -> None:
        """
        No-Op: there is no redis session store any more.

        This use to delete a session by ID.

        No-op; see :meth:`delete`.

        Parameters
        ----------
        session_id : str

        """
        return None

    def validate_session_against_cookie(self, session: domain.Session,
                                        cookie: str) -> None:
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
        if cookie_data['nonce'] != session.nonce \
                or session.user is None \
                or session.user.user_id != cookie_data['user_id']:
            raise InvalidToken('Invalid token; likely a forgery')

    def load(self, cookie: str, decode: bool = True) \
            -> Union[domain.Session, str, bytes]:
        """Load a session from a session cookie.

        Because sessions are stateless, the session is reconstructed from the
        cookie's own signed claims rather than looked up in a store. Only the
        claims carried in the cookie are available: ``user_id``, ``session_id``,
        ``nonce`` and ``expires``. Data that used to live only in the store
        (notably ``authorizations`` and full user details) cannot be restored.
        """
        try:
            cookie_data = self._unpack_cookie(cookie)
            expires = dateutil.parser.parse(cookie_data['expires'])
            user_id = cookie_data['user_id']
            session_id = cookie_data['session_id']
            nonce = cookie_data['nonce']
        except (KeyError, jwt.exceptions.DecodeError) as e:
            raise InvalidToken('Token payload malformed') from e

        if expires <= datetime.now(tz=UTC):
            raise ExpiredToken('Session has expired')

        if not decode:
            return cookie

        session = domain.Session(
            session_id=session_id,
            # username/email are not carried in the cookie; only the user_id
            # is recoverable from a stateless session.
            user=domain.User(user_id=user_id, username='', email=''),
            start_time=datetime.now(tz=UTC),
            end_time=expires,
            nonce=nonce,
        )
        self.validate_session_against_cookie(session, cookie)
        return session

    def load_by_id(self, session_id: str, decode: bool = True) \
            -> Union[domain.Session, str, bytes]:
        """Get session data by session ID.

        Not supported for stateless sessions: without a store there is nothing
        to look up by ID alone. Use :meth:`load` with the session cookie.
        """
        raise UnknownSession(
            'Cannot load a stateless session by ID; use load(cookie)')

    def _encode(self, session_data: dict) -> bytes:
        return jwt.encode(session_data, self._secret)

    def _decode(self, session_jwt: str) -> domain.Session:
        try:
            return domain.Session.parse_obj(
                jwt.decode(session_jwt, self._secret, algorithms=['HS256']))
        except jwt.exceptions.InvalidSignatureError:
            raise InvalidToken('Invalid or corrupted session token')

    def _unpack_cookie(self, cookie: str) -> dict:
        secret = self._secret
        try:
            data = dict(jwt.decode(cookie, secret, algorithms=['HS256']))
        except jwt.exceptions.DecodeError as e:
            raise InvalidToken('Session cookie is malformed') from e
        return data

    def _pack_cookie(self, cookie_data: dict) -> str:
        secret = self._secret
        return jwt.encode(cookie_data, secret)

    @classmethod
    def init_app(cls, app: object = None) -> None:
        """Set default configuration parameters for an application instance."""
        config = get_application_config(app)
        config.setdefault('JWT_SECRET', 'foosecret')
        config.setdefault('SESSION_DURATION', '7200')

    @classmethod
    def get_session(cls, app: object = None) -> 'SessionStore':
        """Get a new session store."""
        config = get_application_config(app)
        secret = config['JWT_SECRET']
        duration = int(config.get('SESSION_DURATION', '7200'))
        return cls('', 0, 0, secret, duration)

    @classmethod
    def current_session(cls) -> 'SessionStore':
        """Get/create a :class:`.SessionStore` for this context."""
        g = get_application_global()
        if not g:
            return cls.get_session()
        if 'session_store' not in g:
            g.session_store = cls.get_session()
        return g.session_store      # type: ignore
