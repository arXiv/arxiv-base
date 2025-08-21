"""Provides API for legacy user sessions."""
from datetime import datetime, timedelta
from pytz import timezone, UTC

import logging

from typing import Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session as SQLAlchemySession

from .. import domain
from ...db import Session as ScopedSession
from . import cookies, util

from ...db.models import TapirSession, TapirSessionsAudit, TapirUser, \
    TapirNickname, Demographic
from .exceptions import UnknownSession, SessionCreationFailed, \
    SessionExpired, InvalidCookie

logger = logging.getLogger(__name__)
EASTERN = timezone('US/Eastern')


def _load(session_id: str,
          db: Optional[SQLAlchemySession] = None
          ) -> TapirSession:
    """Get TapirSession from session id."""
    if db is None:
        db = ScopedSession
    db_session: Optional[TapirSession] = db.query(TapirSession) \
        .filter(TapirSession.session_id == session_id) \
        .first()
    if not db_session:
        logger.debug(f'No session found with id {session_id}')
        raise UnknownSession('No such session')
    return db_session


def _load_audit(session_id: str,
                db: Optional[SQLAlchemySession] = None
                ) -> TapirSessionsAudit:
    """Get TapirSessionsAudit from session id."""
    if db is None:
        db = ScopedSession
    db_sessions_audit: Optional[TapirSessionsAudit] = db.query(TapirSessionsAudit) \
        .filter(TapirSessionsAudit.session_id == session_id) \
        .first()
    if not db_sessions_audit:
        logger.debug(f'No session audit found with id {session_id}')
        raise UnknownSession('No such session audit')
    return db_sessions_audit


def load(cookie: str,
         db: Optional[SQLAlchemySession] = None
         ) -> domain.Session:
    """
    Given a session cookie (from request), load the logged-in user.

    Parameters
    ----------
    cookie : str
        Legacy cookie value passed with the request.
    db : SQLAlchemySession
        SQLAlchemy Session object. Default uses global session.

    Returns
    -------
    :class:`.domain.Session`

    Raises
    ------
    :class:`.legacy.exceptions.SessionExpired`
    :class:`.legacy.exceptions.UnknownSession`

    """
    if db is None:
        db = ScopedSession
    session_id, user_id, ip, issued_at, expires_at, _ = cookies.unpack(cookie)
    logger.debug('Load session %s for user %s at %s',
                 session_id, user_id, ip)

    if expires_at <= datetime.now(tz=UTC):
        raise SessionExpired(f'Session {session_id} has expired in cookie')

    data: Optional[Tuple[TapirUser, TapirSession, TapirNickname, Demographic]]
    data = db.query(TapirUser, TapirSession, TapirNickname, Demographic) \
        .join(TapirSession).join(TapirNickname).join(Demographic) \
        .filter(TapirUser.user_id == user_id) \
        .filter(TapirSession.session_id == session_id ) \
        .first()

    if not data:
        raise UnknownSession('No such user or session')

    db_user, db_session, db_nick, db_profile = data

    if db_session.end_time != 0 and db_session.end_time < util.now():
        raise SessionExpired(f'Session {session_id} has expired in the DB')

    user = domain.User(
        user_id=str(user_id),
        username=db_nick.nickname,
        email=db_user.email,
        name=domain.UserFullName(
            forename=db_user.first_name if db_user.first_name else '',
            surname=db_user.last_name,
            suffix=db_user.suffix_name
        ),
        profile=domain.UserProfile.from_orm(db_profile) if db_profile else None,
        verified=bool(db_user.flag_email_verified)
    )

    authorizations = domain.Authorizations(
        classic=util.compute_capabilities(db_user),
        scopes=util.get_scopes(db_user)
    )
    user_session = domain.Session(session_id=str(db_session.session_id),
                                  start_time=issued_at, end_time=expires_at,
                                  user=user, authorizations=authorizations)
    logger.debug('loaded session %s', user_session.session_id)
    return user_session


def create(authorizations: domain.Authorizations,
           ip: str, remote_host: str, tracking_cookie: str = '',
           user: Optional[domain.User] = None,
           db: Optional[SQLAlchemySession] = None) -> domain.Session:
    """
    Create a new legacy session for an authenticated user.

    Parameters
    ----------
    user : :class:`.User`
    ip : str
        Client IP address.
    remote_host : str
        Client hostname.
    tracking_cookie : str
        Tracking cookie payload from client request.
    db : SQLAlchemySession
        SQLAlchemy Session object. Default uses global session.

    Returns
    -------
    :class:`.Session`

    """
    if user is None:
        raise SessionCreationFailed('Legacy sessions require a user')

    if db is None:
        db =  ScopedSession
    logger.debug('create session for user %s', user.user_id)
    start = datetime.now(tz=UTC)
    end = start + timedelta(seconds=util.get_session_duration())
    try:
        tapir_session = TapirSession(
            user_id=int(user.user_id),
            last_reissue=util.epoch(start),
            start_time=util.epoch(start),
            end_time=0
        )
        db.add(tapir_session)
        db.flush()
        db.refresh(tapir_session)
        tapir_sessions_audit = TapirSessionsAudit(
            session_id=tapir_session.session_id,
            ip_addr=ip,
            remote_host=remote_host,
            tracking_cookie=tracking_cookie
        )
        db.add(tapir_sessions_audit)
        db.commit()
    except Exception as e:
        raise SessionCreationFailed(f'Failed to create: {e}') from e

    session_id = str(tapir_session.session_id)
    user_session = domain.Session(session_id=session_id,
                                  start_time=start, end_time=end,
                                  user=user,
                                  authorizations=authorizations,
                                  ip_address=ip, remote_host=remote_host)
    logger.debug('created session %s', user_session.session_id)
    return user_session


def generate_cookie(session: domain.Session) -> str:
    """
    Generate a cookie from a :class:`domain.Session`.

    Parameters
    ----------
    session : :class:`domain.Session`

    Returns
    -------
    str

    """
    if session.user is None \
       or session.user.user_id is None \
       or session.ip_address is None \
       or session.authorizations is None:
        raise RuntimeError('Cannot generate cookie without an authorized user')

    return cookies.pack(str(session.session_id), session.user.user_id,
                        session.ip_address, session.start_time,
                        str(session.authorizations.classic))


def invalidate(cookie: str,
               db: Optional[SQLAlchemySession] = None
               ) -> None:
    """
    Invalidate a legacy user session.

    Parameters
    ----------
    cookie : str
        Session cookie generated when the session was created.
    db : SQLAlchemySession
        SQLAlchemy Session object. Default uses global session.

    Raises
    ------
    :class:`UnknownSession`
        The session could not be found, or the cookie was not valid.

    """
    try:
        session_id, user_id, ip, _, _, _ = cookies.unpack(cookie)
    except InvalidCookie as e:
        raise UnknownSession('No such session') from e

    invalidate_by_id(session_id, db=db)


def invalidate_by_id(session_id: str, db: Optional[SQLAlchemySession] = None) -> None:
    """
    Invalidate a legacy user session by ID.

    Parameters
    ----------
    session_id : str
        Unique identifier for the session.
    db : SQLAlchemySession
        SQLAlchemy Session object. Default uses global session.

    Raises
    ------
    :class:`UnknownSession`
        The session could not be found, or the cookie was not valid.

    """
    delta = datetime.now(tz=UTC) - datetime.fromtimestamp(0, tz=EASTERN)
    end = delta.total_seconds()
    if db is None:
        db = ScopedSession
    try:
        tapir_session = _load(session_id)
        tapir_session.end_time = end - 1
        db.merge(tapir_session)
        db.commit()
    except NoResultFound as e:
        raise UnknownSession(f'No such session {session_id}') from e
    except SQLAlchemyError as e:
        raise IOError(f'Database error') from e
