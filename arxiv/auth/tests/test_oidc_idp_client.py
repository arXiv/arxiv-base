""" Test the ArxivOidcIdpClient """

import base64
import hashlib
from datetime import datetime, timezone
import traceback

import jwt
import pytest
from pydantic import BaseModel
from pydantic_core._pydantic_core import ValidationError

from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient, generate_pkce_pair
from ..auth.sessions.ng_session_types import NGSessionPayload

from ..user_claims import ArxivUserClaims, ArxivUserClaimsModel


kc_claims_map = {
    "sub": "0cf6ee46-2186-45e0-a960-2012c12d3738",
    "exp": 1722520674,
    "iat": 1722484674,
    "sid": "7985f0a7-fd8c-4dc5-9261-44fd403a9edb",
    # roles = [] ?
    "email_verified": True,
    "email": "testuser@example.com",
    # acc? idt? refresh?
    "first_name": "Test",
    "last_name": "User",
    "username": "TestUser",
}

def test_arxiv_user_claims():
    userClaimsModel = ArxivUserClaimsModel(
        sub = "0cf6ee46-2186-45e0-a960-2012c12d3738",
        exp = 1722520674,
        iat = 1722484674,
        sid = "7985f0a7-fd8c-4dc5-9261-44fd403a9edb",
        # roles = [] ?
        email_verified = True,
        email = "testuser@example.com",
        # acc? idt? refresh?
        first_name = "Test",
        last_name = "User",
        username = "TestUser",
    )
    userClaims = ArxivUserClaims(userClaimsModel)    # ?
    assert userClaims.issued_at
    assert userClaims.expires_at
    assert userClaims.user_id
    # typ 350    
    assert len(userClaims.to_arxiv_token_string) > 300
    assert not userClaims.is_tex_pro
    assert not userClaims.is_approved
    assert not userClaims.is_banned
    assert not userClaims.can_lock
    assert not userClaims.is_owner
    assert not userClaims.is_admin
    assert not userClaims.is_mod
    assert not userClaims.is_legacy_user
    assert not userClaims.is_public_user
    assert userClaims.classic_capability_code == 0
    assert len(userClaims._roles) == 0
    assert userClaims.id_token == None
    assert userClaims.refresh_token == None
    assert userClaims.email
    assert userClaims.email_verified
    assert userClaims.first_name
    assert userClaims.last_name
    assert userClaims.client_ip4v == "0.0.0.0" # typo?
    assert userClaims.tapir_session_id is None
    userClaims.tapir_session_id = 1234
    assert userClaims.tapir_session_id == 1234
    assert ArxivUserClaims.from_arxiv_token_string(userClaims.to_arxiv_token_string) 
    # Throws
    with pytest.raises(ValidationError):
        # divide(3, 0)
        print( ArxivUserClaims.from_keycloak_claims({}, kc_claims_map, "ipv4") )
    assert userClaims.is_expired()
    assert userClaims.is_expired(datetime.now(timezone.utc))
    userClaims.update_claims("last_name", "NewLastName")
    encoded: str = userClaims.encode_jwt_token("secret")
    assert encoded.startswith("eyJhb")
    assert len(encoded) < 4096
    userClaims.update_keycloak_access_token({'acc': 12345})
    assert userClaims.domain_session # a complicated object

    # Round-trip encode/decode. The fixture above is intentionally expired (for the
    # is_expired asserts), but decode now enforces the JWT `exp`, so use a fresh token
    # with a future exp here.
    now = int(datetime.now(timezone.utc).timestamp())
    freshClaims = ArxivUserClaims(ArxivUserClaimsModel(
        sub = "0cf6ee46-2186-45e0-a960-2012c12d3738",
        exp = now + 3600,
        iat = now,
        sid = "7985f0a7-fd8c-4dc5-9261-44fd403a9edb",
        email_verified = True,
        email = "testuser@example.com",
        first_name = "Test",
        last_name = "User",
        username = "TestUser",
    ))
    encoded = freshClaims.encode_jwt_token("secret")
    # I need a session (using None fails) here
    # userClaims.set_tapir_session(arxivSession)
    # ArxivUserClaims.decode_jwt_payload({tokens}, jwt_payload, secret, [algorithm])
    tokens = {}
    decoded = ArxivUserClaims.decode_jwt_payload(tokens, encoded, 'secret')
    assert decoded
    assert decoded.user_id == "0cf6ee46-2186-45e0-a960-2012c12d3738"
    assert decoded.email == "testuser@example.com"
    payload_ng = jwt.decode(encoded, 'secret', algorithms = ['HS256'])
    assert NGSessionPayload.model_validate(payload_ng)


def test_decode_jwt_payload_expired():
    """A token whose `exp` is in the past must raise PyJWT's ExpiredSignatureError on decode."""
    now = int(datetime.now(timezone.utc).timestamp())
    expiredClaims = ArxivUserClaims(ArxivUserClaimsModel(
        sub = "0cf6ee46-2186-45e0-a960-2012c12d3738",
        exp = now - 3600,   # expired one hour ago
        iat = now - 7200,
        sid = "7985f0a7-fd8c-4dc5-9261-44fd403a9edb",
        email_verified = True,
        email = "testuser@example.com",
        first_name = "Test",
        last_name = "User",
        username = "TestUser",
    ))
    encoded = expiredClaims.encode_jwt_token("secret")
    with pytest.raises(jwt.ExpiredSignatureError):
        ArxivUserClaims.decode_jwt_payload({}, encoded, 'secret')


def test_arxiv_oidc_idp_client():
    redirect_uri = "https://example.com"
    client = ArxivOidcIdpClient(redirect_uri)
    # assert client.oidc().startswith("https://openid.arxiv.org")
    assert client.oidc.endswith("openid-connect")
    assert client.authn_url.endswith("/auth")
    assert client.token_url.endswith("/token")
    assert client.token_introspect_url.endswith("/token/introspect")
    assert client.certs_url.endswith("/certs")
    assert client.user_info_url.endswith("/userinfo")
    
    userClaimsModel = ArxivUserClaimsModel(
        sub = "0cf6ee46-2186-45e0-a960-2012c12d3738",
        exp = 1722520674,
        iat = 1722484674,
        sid = "7985f0a7-fd8c-4dc5-9261-44fd403a9edb",
        # roles = [] ?
        email_verified = True,
        email = "testuser@example.com",
        # acc? idt? refresh?
        first_name = "Test",
        last_name = "User",
        username = "TestUser",
    )
    userClaims = ArxivUserClaims(userClaimsModel)    # ?
    assert client.logout_url(userClaims)
    assert client.login_url
    # Requires internet
    # assert client.server_certs
    # assert client.get_public_key()
    token = client.acquire_idp_token("test")
    # assert client.validate_access_token(token)
    idp_token = token
    kc_cliams = {"abc": "1234"}
    client_ipv4 = "This is a test"
    # need better kc_claims
    # print( client.to_arxiv_user_claims(idp_token, kc_cliams, client_ipv4))
    code = "abcd"
    assert client.from_code_to_user_claims(code, client_ipv4) == None
    user = None
    assert client.logout_user(user) == False
    refresh_token = "abcd"
    assert client.refresh_access_token(refresh_token) is None


def test_pkce():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) == 43
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    assert challenge == expected

    client = ArxivOidcIdpClient("https://example.com/callback")
    url = client.login_url_with_pkce(challenge, state="random-state")
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert "state=random-state" in url
