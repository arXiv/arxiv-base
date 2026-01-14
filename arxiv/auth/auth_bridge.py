from . import domain
from .legacy.util import _compute_capabilities
from .user_claims import ArxivUserClaims
from .legacy.authenticate import instantiate_tapir_user, _get_user_by_user_id
from ..db import transaction
from .legacy.sessions import create as legacy_create_session
from .legacy.cookies import pack as legacy_pack


def populate_user_claims(user_claims: ArxivUserClaims):
    """
    Populate the user's claims to the universe
    """
    with transaction():
        passdata = _get_user_by_user_id(user_claims.user_id)
        d_user, d_auth = instantiate_tapir_user(passdata)

        session: domain.Session = legacy_create_session(
            d_auth, user=d_user, tracking_cookie=user_claims.session_id
        )
        user_claims.update_claims("tapir_session_id", session.session_id)


def bake_cookies(user_claims: ArxivUserClaims) -> (str, str):
    cit_cookie = legacy_pack(
        user_claims.tapir_session_id,
        issued_at=user_claims.issued_at,
        user_id=user_claims.user_id,
        capabilities=_compute_capabilities(
            user_claims.is_admin, user_claims.email_verified, user_claims.is_god
        ),
    )

    return cit_cookie, ArxivUserClaims.to_arxiv_token_string
