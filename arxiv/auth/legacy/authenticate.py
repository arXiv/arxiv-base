"""Provide an API for user authentication using the legacy database."""

from typing import Optional, Generator, Tuple
import hashlib
from base64 import b64encode, b64decode
from contextlib import contextmanager
from datetime import datetime
import logging

from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

from . import util, endorsements
from .. import domain
from ..auth import scopes

from . passwords import check_password, is_ascii
from arxiv.db import session
from arxiv.db.models import TapirUser, TapirUsersPassword, TapirPermanentToken, \
    TapirNickname, Demographic
from .exceptions import NoSuchUser, AuthenticationFailed, \
    PasswordAuthenticationFailed, Unavailable

logger = logging.getLogger(__name__)

PassData = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]


def authenticate(username_or_email: Optional[str] = None,
                 password: Optional[str] = None, token: Optional[str] = None) \
        -> Tuple[domain.User, domain.Authorizations]:
    """
    Validate username/password. If successful, retrieve user details.

    Parameters
    ----------
    username_or_email : str
        Users may log in with either their username or their email address.
    password : str
        Password (as entered). Danger, Will Robinson!
    token : str
        Alternatively, the user may provide a bearer token. This is currently
        used to support "permanent" sessions, in which the token is used to
        "automatically" log the user in (i.e. without entering credentials).

    Returns
    -------
    :class:`domain.User`
    :class:`domain.Authorizations`

    Raises
    ------
    :class:`AuthenticationFailed`
        Failed to authenticate user with provided credentials.
    :class:`Unavailable`
        Unable to connect to DB.
    """
    try:
        if username_or_email and password:
            passdata = _authenticate_password(username_or_email, password)
        # The "tapir permanent token" is effectively a bearer token. If passed,
        # a new session will be "automatically" created (from the user's
        # perspective).
        elif token:
            db_token = _authenticate_token(token)
            passdata = _get_user_by_user_id(db_token.user_id)
        else:
            logger.debug('Neither username/password nor token provided')
            raise AuthenticationFailed('Username+password or token required')
    except OperationalError as e:
        # Note OperationalError can be a lot of different things and not just
        # the DB being unavailable. So this message can be deceptive.
        raise Unavailable('Database is temporarily unavailable') from e
    except Exception as ex:
        raise AuthenticationFailed() from ex

    db_user, _, db_nick, db_profile = passdata
    user = domain.User(
        user_id=str(db_user.user_id),
        username=db_nick.nickname,
        email=db_user.email,
        name=domain.UserFullName(
            forename=db_user.first_name,
            surname=db_user.last_name,
            suffix=db_user.suffix_name
        ),
        profile=domain.UserProfile.from_orm(db_profile) if db_profile else None,
        verified=bool(db_user.flag_email_verified)
    )
    auths = domain.Authorizations(
        classic=util.compute_capabilities(db_user),
        scopes=util.get_scopes(db_user),
        endorsements=endorsements.get_endorsements(user)
    )
    return user, auths


def _authenticate_token(token: str) -> TapirPermanentToken:
    """
    Authenticate using a permanent token.

    Parameters
    ----------
    token : str

    Returns
    -------
    :class:`.TapirUser`
    :class:`.TapirPermanentToken`
    :class:`.TapirNickname`
    :class:`.Demographic`

    Raises
    ------
    :class:`AuthenticationFailed`
        Raised if the token is malformed, or there is no corresponding token
        in the database.

    """
    try:
        user_id, secret = token.split('-')
    except ValueError as e:
        raise AuthenticationFailed('Token is malformed') from e
    try:
        return _get_token(user_id, secret)
    except NoSuchUser as e:
        logger.debug('Not a valid permanent token')
        raise AuthenticationFailed('Invalid token') from e


def _authenticate_password(username_or_email: str, password: str) -> PassData:
    """
    Authenticate using username/email and password.

    Parameters
    ----------
    username_or_email : str
        Either the email address or username of the authenticating user.
    password : str

    Returns
    -------
    :class:`.TapirUser`
    :class:`.TapirUsersPassword`
    :class:`.TapirNickname`

    Raises
    ------
    :class:`AuthenticationFailed`
        Raised if the user does not exist or the password is incorrect.
    :class:`RuntimeError`
        Raised when other problems arise.

    """
    logger.debug(f'Authenticate with password, user: {username_or_email}')

    if not password:
        raise ValueError('Passed empty password')
    if not isinstance(password, str):
        raise ValueError('Passed non-str password: {type(password)}')
    if not is_ascii(password):
        raise ValueError('Password non-ascii password')

    if not username_or_email:
        raise ValueError('Passed empty username_or_email')
    if not isinstance(password, str):
        raise ValueError('Passed non-str username_or_email: {type(username_or_email)}')
    if len(username_or_email) > 255:
        raise ValueError(f'Passed username_or_email too long: len {len(username_or_email)}')
    if not is_ascii(username_or_email):
        raise ValueError('Passed non-ascii username_or_email')

    if '@' in username_or_email:
        passdata = _get_user_by_email(username_or_email)
    else:
        passdata = _get_user_by_username(username_or_email)

    db_user, db_pass, db_nick, db_profile = passdata
    logger.debug(f'Got user with user_id: {db_user.user_id}')
    try:
        if check_password(password, db_pass.password_enc):
            return passdata
    except PasswordAuthenticationFailed as e:
        raise AuthenticationFailed('Invalid username or password') from e


def _get_user_by_user_id(user_id: int) -> PassData:
    tapir_user: TapirUser = session.query(TapirUser) \
        .filter(TapirUser.user_id == int(user_id)) \
        .filter(TapirUser.flag_approved == 1) \
        .filter(TapirUser.flag_deleted == 0) \
        .filter(TapirUser.flag_banned == 0) \
        .first()
    return _get_passdata(tapir_user)


def _get_user_by_email(email: str) -> PassData:
    if not email or '@' not in email:
        raise ValueError("must be an email address")
    tapir_user: TapirUser = session.query(TapirUser) \
        .filter(TapirUser.email == email) \
        .filter(TapirUser.flag_approved == 1) \
        .filter(TapirUser.flag_deleted == 0) \
        .filter(TapirUser.flag_banned == 0) \
        .first()
    return _get_passdata(tapir_user)


def _get_user_by_username(username: str) -> PassData:
    """Username is the tapir nickname."""
    if not username or '@' in username:
        raise ValueError("username must not contain a @")
    tapir_nick = session.query(TapirNickname) \
            .filter(TapirNickname.nickname == username) \
            .filter(TapirNickname.flag_valid == 1) \
            .first()
    if not tapir_nick:
        raise NoSuchUser('User lacks a nickname')

    tapir_user = session.query(TapirUser) \
                .filter(TapirUser.user_id == tapir_nick.user_id) \
                .filter(TapirUser.flag_approved == 1) \
                .filter(TapirUser.flag_deleted == 0) \
                .filter(TapirUser.flag_banned == 0) \
                .first()
    return _get_passdata(tapir_user)


def _get_passdata(tapir_user: TapirUser) -> PassData:
    """
    Retrieve password, nick name and profile data.

    Parameters
    ----------
    username_or_email : str

    Returns
    -------
    :class:`.TapirUser`
    :class:`.TapirUsersPassword`
    :class:`.TapirNickname`
    :class:`.Demographic`

    Raises
    ------
    :class:`NoSuchUser`
        Raised when the user cannot be found.
    :class:`RuntimeError`
        Raised when other problems arise.

    """
    if not tapir_user:
        raise NoSuchUser('User does not exist')

    tapir_nick = session.query(TapirNickname) \
            .filter(TapirNickname.user_id ==tapir_user.user_id) \
            .filter(TapirNickname.flag_valid == 1) \
            .first()
    if not tapir_nick:
        raise NoSuchUser('User lacks a nickname')

    tapir_password: TapirUsersPassword = session.query(TapirUsersPassword) \
        .filter(TapirUsersPassword.user_id == tapir_user.user_id) \
        .first()
    if not tapir_password:
        raise RuntimeError(f'Missing password')

    tapir_profile: Demographic = session.query(Demographic) \
        .filter(Demographic.user_id == tapir_user.user_id) \
        .first()
    return tapir_user, tapir_password, tapir_nick, tapir_profile


def _invalidate_token(user_id: str, secret: str) -> None:
    """
    Invalidate a user's permanent login token.

    Parameters
    ----------
    user_id : str
    secret : str

    Raises
    ------
    :class:`NoSuchUser`
        Raised when the token or user cannot be found.

    """
    db_token = _get_token(user_id, secret)
    db_token.valid = 0
    session.add(db_token)
    session.commit()


def _get_token(user_id: str, secret: str) -> TapirPermanentToken:
    """
    Retrieve a user's permanent token.

    User ID and token are used together as the primary key for the token.

    Parameters
    ----------
    user_id : str
    secret : str
    valid : int
        (default: 1)

    Returns
    -------
    :class:`.TapirPermanentToken`

    Raises
    ------
    :class:`NoSuchUser`
        Raised when the token or user cannot be found.

    """
    if not user_id.isdigit():
        raise ValueError("user_id must be digits")
    if not user_id:
        raise ValueError("user_id must not be empty")
    if len(user_id) > 50:
        raise ValueError("user_id too long")
    if len(secret) > 40:
        raise ValueError("secret too long")

    db_token: TapirPermanentToken = session.query(TapirPermanentToken) \
        .filter(TapirPermanentToken.user_id == user_id) \
        .filter(TapirPermanentToken.secret == secret) \
        .filter(TapirPermanentToken.valid == 1) \
        .first()    # The token must still be valid.
    if not db_token:
        raise NoSuchUser('No such token')
    else:
        return db_token
