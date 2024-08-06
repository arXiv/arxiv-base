"""
User claims.

The idea is that, when a user is authenticated, the claims represent who that is.
"""

# This needs to be tied to the tapir user
#

import json
from datetime import datetime, timezone


def kc_cliams_to_arxiv_token_data(kc_claims: dict) -> dict:
    """Turn keycloak access token into arXiv claims.

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
    """

    _role_to_authorization: dict = {
        "AllowTexProduced": "tex_pro",
        "Approved": "approved",
        "Banned": "banned",
        "CanLock": "can_lock",
        "EditSystem": "is_god",
        "EditUser": "is_admin",
        "Legacy user": "legacy",
        "Public user": "public",
    }

    data = {
        "expires_at": datetime.utcfromtimestamp(kc_claims.get('exp', 0)),
        "issued_at": datetime.utcfromtimestamp(kc_claims.get('iat', 0)),
        "client_id": kc_claims.get('azp'),
        "session_id": kc_claims.get('sid'),
        "user_id": kc_claims.get('sub'),
        "issuer": kc_claims.get('iss'),
        "email_verified": kc_claims.get('email_verified'),
        "login_name": kc_claims.get('preferred_username'),
        "email": kc_claims.get('email'),
        "name": kc_claims.get('name'), # human full name
    }

    for role in kc_claims.get('realm_access', {}).get('roles', []):
        if role in _role_to_authorization:
            data[_role_to_authorization[role]] = True
    return data


class ArxivUserClaims:
    """
    arXiv logged in user claims
    """
    _claims: dict

    tapir_session_id: str
    issued_at: datetime
    client_id: str
    session_id: str
    user_id: str
    email_verified: bool
    login_name: str
    email: str
    name: str

    tex_pro: bool
    approved: bool
    banned: bool
    can_lock: bool
    is_god: bool
    is_admin: bool
    legacy: bool
    public: bool

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
            def getter(self):
                return self._claims.get(name)
            setattr(self.__class__, name, property(getter))


    @property
    def to_arxiv_token_string(self) -> str:
        return json.dumps(self._claims)

    @classmethod
    def from_arxiv_token_string(cls, token: str) -> 'ArxivUserClaims':
        return cls(json.loads(token))

    @classmethod
    def from_keycloak_claims(cls, kc_cliams: dict, access_token: str, refresh_token: str) -> 'ArxivUserClaims':
        claims = kc_cliams_to_arxiv_token_data(kc_cliams)
        claims['access_token'] = access_token
        claims['refresh_token'] = refresh_token
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


    pass
