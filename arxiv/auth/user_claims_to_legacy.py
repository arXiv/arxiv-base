from typing import Tuple, Optional
from .legacy.authenticate import PassData, _get_user_by_email, instantiate_tapir_user, NoSuchUser, _get_user_by_user_id
from .legacy.sessions import (
    create as create_legacy_session,
    generate_cookie as generate_legacy_cookie,
    invalidate as legacy_invalidate,
)
from ..db import transaction


from .user_claims import ArxivUserClaims
from .domain import Authorizations, Session

# PassData = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]

def create_tapir_session_from_user_claims(user_claims: ArxivUserClaims,
                                          client_host: str,
                                          client_ip: str,
                                          tracking_cookie: str = '',
                                          ) -> Optional[Tuple[str, Session]]:
    """
    Using the legacy tapir models, establish the session and return the legacy cookie.

    You need to be in a transaction.
    """
    passdata = None
    try:
        passdata = _get_user_by_user_id(user_claims.user_id)
    except NoSuchUser:
        pass

    if passdata is None:
        # passdata = create_legacy_user(user_claims)
        return None

    tapir_user, legacy_auth = instantiate_tapir_user(passdata)
    session: Session = create_legacy_session(legacy_auth, client_ip, client_host,
                                             tracking_cookie=tracking_cookie,
                                             user=tapir_user)
    legacy_cookie = generate_legacy_cookie(session)
    return legacy_cookie, session


def create_legacy_user(user_claims: ArxivUserClaims) -> PassData:
    """
    Very likely, this isn't going to happen here.
    """
    return "TBD"


def terminate_legacy_session(legacy_cookie: str) -> None:
    """
    This is an alias to existing session killer.
    """
    with transaction() as session:
        legacy_invalidate(legacy_cookie)
