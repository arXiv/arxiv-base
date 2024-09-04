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
from typing import Any, Optional, List, Tuple

import jwt


def get_roles(realm_access: dict) -> Tuple[str, Any]:
    return 'roles', realm_access['roles']


claims_map = {
    'sub': 'sub',
    'exp': 'exp',
    'iat': 'iat',
    'realm_access': get_roles,
    'email_verified': 'email_p',
    'email': 'email',
    "access_token": "acc",
    "id_token": "idt",
    "refresh_token": "refresh",
}

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
    def expires_at(self) -> datetime:
        return datetime.utcfromtimestamp(float(self._claims.get('exp', 0)))

    @property
    def issued_at(self) -> datetime:
        return datetime.utcfromtimestamp(float(self._claims.get('iat', 0)))

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
        return self._claims.get('roles', [])

    @property
    def id_token(self) -> str:
        """
        Keycloak id_token
        """
        return self._claims.get('idt', "")

    @property
    def access_token(self) -> str:
        """
        Keycloak access (bearer) token
        """
        return self._claims.get('acc', '')

    @property
    def refresh_token(self) -> str:
        """
        Keycloak refresh token
        """
        return self._claims.get('refresh', '')

    @classmethod
    def from_arxiv_token_string(cls, token: str) -> 'ArxivUserClaims':
        return cls(json.loads(token))

    @classmethod
    def from_keycloak_claims(cls,
                             idp_token: Optional[dict] = None,
                             kc_claims: Optional[dict] = None) -> 'ArxivUserClaims':
        """Make the user cliams from the IdP token and user claims

        The claims need to be compact as the cookie size is limited to 4096, tossing "uninteresting"
        """
        claims = {}
        # Flatten the idp token and claims
        mushed = idp_token.copy() if idp_token else {}
        if kc_claims:
            mushed.update(kc_claims)

        for key, mapper in claims_map.items():
            if key not in mushed:
                # This may be worth logging.
                continue
            value = mushed.get(key)
            if callable(mapper):
                mapped_key, mapped_value = mapper(value)
                if mapped_key and mapped_value:
                    claims[mapped_key] = mapped_value
            elif key in mushed:
                claims[mapper] = value
        return cls(claims)

    def is_expired(self, when: datetime | None = None) -> bool:
        """
        Check if the claims is expired
        """
        if when is None:
            when = datetime.now(timezone.utc)
        return when > self.expires_at

    def update_claims(self, tag: str, value: str) -> None:
        """
        Add a value to the claims. Somewhat special so use it with caution
        """
        self._claims[tag] = value
        self._create_property(tag)

    def encode_jwt_token(self, secret: str, algorithm: str = 'HS256') -> str:
        """packing user claims"""
        claims = self._claims.copy()
        del claims['idt']
        del claims['acc']
        if 'refresh' in claims:
            del claims['refresh']
        payload = jwt.encode(claims, secret, algorithm=algorithm)
        assert(',' not in self.id_token)
        assert(',' not in self.access_token)
        assert(',' not in payload)
        tokens = [self.id_token, self.access_token, payload]
        if self.refresh_token:
            assert (',' not in self.refresh_token)
            tokens.append(self.refresh_token)
        token = ",".join(tokens)
        if len(token) > 4096:
            raise ValueError(f'JWT token is too long {len(token)} bytes')
        return token

    @classmethod
    def unpack_token(cls, token: str) -> Tuple[dict, str]:
        chunks = token.split(',')
        if len(chunks) < 3:
            raise ValueError(f'Token is invalid')
        tokens = {
            'idt': chunks[0],
            'acc':  chunks[1]
        }
        if len(chunks) > 3:
            tokens['refsesh'] = chunks[3]
        return tokens, chunks[2]

    @classmethod
    def decode_jwt_payload(cls, claims: dict, jwt_payload: str, secret: str, algorithm: str = 'HS256') -> "ArxivUserClaims":
        payload = jwt.decode(jwt_payload, secret, algorithms = [algorithm])
        claims.update(payload)
        return cls(claims)


    def update_keycloak_access_token(self, updates: dict) -> None:
        self._claims['acc'] = updates['acc']
        return


    pass
