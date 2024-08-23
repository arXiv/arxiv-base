from typing import Tuple, Optional
from .legacy.authenticate import PassData, _get_user_by_email, instantiate_tapir_user
from .legacy.sessions import (
    create as create_legacy_session,
    generate_cookie as generate_legacy_cookie,
    invalidate as legacy_invalidate,
)


from .user_claims import ArxivUserClaims
from .domain import Authorizations, Session

# PassData = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]

def create_tapir_session_from_user_claims(user_claims: ArxivUserClaims) -> Optional[Tuple[str, Session]]:
    """
    Using the legacy tapir models, establish the session and return the legacy cookie.
    """
    passdata  = _get_user_by_email(user_claims.email)
    if passdata is None:
        passdata = create_legacy_user(user_claims)
    tapir_user, legacy_auth = instantiate_tapir_user(passdata)
    session: Session = create_legacy_session(legacy_auth, user=tapir_user)
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
    legacy_invalidate(legacy_cookie)
