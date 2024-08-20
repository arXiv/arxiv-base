"""
User claims.

The idea is that, when a user is authenticated, the claims represent who that is.
Keycloak:

    unpacked access token looks like this
    {
        'exp': 1722520674,
        'iat': 1722484674,
        'auth_time': 1722484674,
        'jti': 'a45020b9-d7c4-4e28-9166-e95897007f4f',
        'iss': 'https://keycloak-service-6lhtms3oua-uc.a.run.app/realms/arxiv',
        'sub': '0cf6ee46-2186-45e0-a960-2012c12d3738',
        'typ': 'Bearer',
        'azp': 'arxiv-user',
        'sid': '7985f0a7-fd8c-4dc5-9261-44fd403a9edb',
        'acr': '1',
        'allowed-origins': ['http://localhost:5000'],
        'realm_access':
            {
                'roles': ['Approved', 'AllowTexProduced']},
        'scope': 'email profile',
        'email_verified': True,
        'name': 'Test User',
        'groups': ['Approved', 'AllowTexProduced'],
        'preferred_username': 'testuser',
        'given_name': 'Test',
        'family_name': 'User',
        'email': 'testuser@example.com'
    }

    Tapir cookie data
    return self._pack_cookie({
       'user_id': session.user.user_id,
        'session_id': session.session_id,
        'nonce': session.nonce,
        'expires': session.end_time.isoformat()
    })

"""

# This needs to be tied to the tapir user
#

import json
from datetime import datetime, timezone
from typing import Any, Optional, List

import jwt


class ArxivUserClaims:
    """
    arXiv logged in user claims
    """
    _claims: dict

    tapir_session_id: str
    email_verified: bool
    login_name: str
    email: str
    name: str

    def __init__(self, claims: dict) -> None:
        """
        IdP token
        """
        self._claims = claims.copy()
        for key in self._claims.keys():
            self._create_property(key)
        pass


    def _create_property(self, name: str) -> None:
        if not hasattr(self.__class__, name):
            def getter(self: "ArxivUserClaims") -> Any:
                return self._claims.get(name)
            setattr(self.__class__, name, property(getter))

    @property
    def expires_at(self) -> str:
        return datetime.utcfromtimestamp(self._claims.get('exp', 0)).isoformat()

    @property
    def issued_at(self) -> str:
        return datetime.utcfromtimestamp(self._claims.get('iat', 0)).isoformat()

    @property
    def client_id(self) -> Optional[str]:
        return self._claims.get('azp')

    @property
    def session_id(self) -> Optional[str]:
        return self._claims.get('sid')

    @property
    def user_id(self) -> Optional[str]:
        return self._claims.get('sub')

    # jwt.encode/decode serialize/deserialize dict, not string so not really needed
    @property
    def to_arxiv_token_string(self) -> Optional[str]:
        return json.dumps(self._claims)

    @property
    def is_tex_pro(self) -> bool:
        return "AllowTexProduced" in self._roles

    @property
    def is_approved(self) -> bool:
        return "Approved" in self._roles

    @property
    def is_banned(self) -> bool:
        return "Banned" in self._roles

    @property
    def can_lock(self) -> bool:
        return "CanLock" in self._roles

    @property
    def is_owner(self) -> bool:
        return "Owner" in self._roles

    @property
    def is_admin(self) -> bool:
        return "Administrator" in self._roles

    @property
    def is_mod(self) -> bool:
        return "Moderator" in self._roles

    @property
    def is_legacy_user(self) -> bool:
        return "Legacy user" in self._roles

    @property
    def is_public_user(self) -> bool:
        return "Public user" in self._roles

    @property
    def _roles(self) -> List[str]:
        return self._claims.get('realm_access', {}).get('roles', [])

    @property
    def id_token(self) -> str:
        """
        id_token is jti of keycloak. Not sure other IdP's use this but I think this is handy and
        clarifies somwhat cryptic 3-letter tags of access token.
        """
        return self._claims.get('jti', '')

    @classmethod
    def from_arxiv_token_string(cls, token: str) -> 'ArxivUserClaims':
        return cls(json.loads(token))

    @classmethod
    def from_keycloak_claims(cls, kc_cliams: dict, access_token: str, _refresh_token: str) -> 'ArxivUserClaims':
        claims = kc_cliams.copy()
        claims['access_token'] = access_token
        # claims['refresh_token'] = refresh_token
        return cls(claims)

    def is_expired(self, when: datetime | None = None) -> bool:
        """
        Check if the claims is expired
        """
        exp = self._claims.get("expires_at")
        if exp is None:
            return False
        exp_datetime = datetime.fromtimestamp(exp, timezone.utc)
        if when is None:
            when = datetime.now(timezone.utc)
        return when > exp_datetime

    def update_claims(self, tag: str, value: str) -> None:
        """
        Add a value to the claims. Somewhat special so use it with caution
        """
        self._claims[tag] = value
        self._create_property(tag)

    def encode_jwt_token(self, secret: str, algorithm: str = 'HS256') -> str:
        return jwt.encode(self._claims, secret, algorithm=algorithm)

    @classmethod
    def decode_jwt_token(cls, token: str, secret: str, algorithm: str = 'HS256') -> "ArxivUserClaims":
        return cls(jwt.decode(token, secret, algorithms=[algorithm]))

    pass
