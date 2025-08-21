from typing import Tuple, Optional
from logging import getLogger
from .legacy.authenticate import PassData, _get_user_by_email, instantiate_tapir_user, NoSuchUser, _get_user_by_user_id
from .legacy.sessions import (
    create as create_legacy_session,
    generate_cookie as generate_legacy_cookie,
    invalidate as legacy_invalidate,
)
from sqlalchemy.orm import Session as SQLAlchemySession

from .user_claims import ArxivUserClaims
from .domain import Session as DomainSession

# PassData = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]

def create_tapir_session_from_user_claims(db: SQLAlchemySession,
                                          user_claims: ArxivUserClaims,
                                          client_host: str,
                                          client_ip: str,
                                          tracking_cookie: str = '',
                                          ) -> Optional[Tuple[str, DomainSession]]:
    """
    Using the legacy tapir models, establish the session and return the legacy cookie.

    You need to be in a transaction.
    """
    logger = getLogger(__name__)
    passdata = None
    try:
        user_id = int(user_claims.user_id)
    except ValueError:
        user_id = user_claims.user_id
        logger.warning("create_tapir_session_from_user_claims: User ID '%s' is not int", user_id)
        pass

    try:
        passdata = _get_user_by_user_id(user_id)
    except NoSuchUser:
        pass

    if passdata is None:
        # passdata = create_legacy_user(user_claims)
        return None

    tapir_user, legacy_auth = instantiate_tapir_user(passdata)
    session: DomainSession = create_legacy_session(
        legacy_auth, client_ip, client_host,
        tracking_cookie=tracking_cookie, user=tapir_user, db=db)
    legacy_cookie = generate_legacy_cookie(session)
    return legacy_cookie, session

