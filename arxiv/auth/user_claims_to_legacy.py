from .legacy.authenticate import PassData, _get_user_by_email, instantiate_tapir_user
from .legacy.sessions import (
    create as create_legacy_session,
    generate_cookie as generate_legacy_cookie)

from .user_claims import ArxivUserClaims
from .domain import Authorizations, Session

# PassData = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]

def create_tapir_session_from_user_claims(user_claims: ArxivUserClaims) -> str | None:
    """
    Using the legacy tapir models, establish the session and return the cookie.
    """
    passdata  = _get_user_by_email(user_claims.email)
    if passdata is None:
        return None
    tapir_user: Authorizations, legacy_auth = instantiate_tapir_user(passdata)
    session: Session = create_legacy_session(legacy_auth, user=tapir_user)
    legacy_cookie = generate_legacy_cookie(session)
    return legacy_cookie
