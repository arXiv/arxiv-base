"""
User claims.
When a user is authenticated, the claims represent who that is.

In other words, the user claims is a Python object from the identity cookie.


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
from pydantic import BaseModel
import jwt
from . import domain
from .auth.sessions.ng_session_types import NGSessionPayload
from ..db.models import TapirPolicyClass
from .auth import scopes, tokens
from .auth.tokens import encode as ng_encode, decode as ng_decode
from ..auth.domain import Session as ArxivSession


class ArxivUserClaimsModel(BaseModel):
    sub: str            # User ID (subject)
    exp: int            # Expiration
    iat: int            # Issued at (time)
    sid: str            # Keycloak session ID
    roles: Optional[List[str]] = None
    email_verified: bool
    email: str

    acc: Optional[str] = None      # Access token
    idt: Optional[str] = None      # ID Token
    refresh: Optional[str] = None  # Refresh tokel

    first_name: str
    last_name: str
    username: str

    client_ipv4: Optional[str] = None
    ts_id: Optional[int] = None    # Tapir session ID

    class Config:
        extra = "ignore"
        populate_by_name = True
        from_attributes = True


def get_roles(realm_access: dict) -> Tuple[str, Any]:
    return 'roles', realm_access['roles']


claims_map = {
    'sub': 'sub',
    'exp': 'exp',
    'iat': 'iat',
    'sid': 'sid',
    'realm_access': get_roles,
    'email_verified': 'email_verified',
    'email': 'email',
    "access_token": "acc",
    "id_token": "idt",
    "refresh_token": "refresh",
    "given_name": "first_name",
    "family_name": "last_name",
    "preferred_username": "username",
    "client_ipv4": "client_ipv4",
}

NG_COOKIE_HITCHHIKER_NAME = 'nonce'

class ArxivUserClaims:
    """
    arXiv logged in user claims
    """
    _claims: ArxivUserClaimsModel

    # tapir_session_id: str
    # email_verified: bool
    # login_name: str
    # email: str
    # name: str
    _domain_session: Optional[domain.Session]

    def __init__(self, claims: ArxivUserClaimsModel) -> None:
        """
        IdP token
        """
        self._domain_session = None
        self._claims = claims.model_copy()
        pass


    @property
    def expires_at(self) -> datetime:
        """Keycloak token expiration time"""
        return datetime.fromtimestamp(float(self._claims.exp), tz=timezone.utc)

    @property
    def issued_at(self) -> datetime:
        """Keycloak token issue timestamp"""
        return datetime.fromtimestamp(float(self._claims.iat), tz=timezone.utc)

    @property
    def kc_session_id(self) -> Optional[str]:
        """Keycloak session ID"""
        return self._claims.sid

    @property
    def user_id(self) -> Optional[str]:
        """Keycloak/Tapir user ID"""
        return self._claims.sub

    # jwt.encode/decode serialize/deserialize dict, not string so not really needed
    # you should not use this for real. okay for testing
    @property
    def to_arxiv_token_string(self) -> Optional[str]:
        return json.dumps(self._claims.model_dump())

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
    def classic_capability_code(self) -> int:
        roles = self._claims.roles if self._claims.roles else []
        for policy_class in TapirPolicyClass.POLICY_CLASSES:
            if policy_class["name"] in roles:
                return policy_class["class_id"]
        return 0

    @property
    def _roles(self) -> List[str]:
        return self._claims.roles if self._claims.roles else []

    @property
    def id_token(self) -> str:
        """
        Keycloak id_token
        """
        return self._claims.idt

    @property
    def access_token(self) -> str:
        """
        Keycloak access (bearer) token
        """
        return self._claims.acc

    @property
    def refresh_token(self) -> str:
        """
        Keycloak refresh token
        """
        return self._claims.refresh

    @property
    def email(self) -> str:
        return self._claims.email

    @property
    def email_verified(self) -> bool:
        return self._claims.email_verified

    @property
    def username(self) -> str:
        return self._claims.username

    @property
    def first_name(self) -> str:
        return self._claims.first_name

    @property
    def last_name(self) -> str:
        return self._claims.last_name

    @property
    def client_ip4v(self) -> str:
        return self._claims.client_ipv4 if self._claims.client_ipv4 else "0.0.0.0"

    @property
    def tapir_session_id(self) -> int | None:
        return self._claims.ts_id

    @tapir_session_id.setter
    def tapir_session_id(self, ts_id: int) -> None:
        setattr(self._claims, 'ts_id', ts_id)

    @classmethod
    def from_arxiv_token_string(cls, token: str) -> 'ArxivUserClaims':
        return cls(ArxivUserClaimsModel.model_validate(json.loads(token)))

    @classmethod
    def from_keycloak_claims(cls,
                             idp_token: Optional[dict] = None,
                             kc_claims: Optional[dict] = None,
                             client_ipv4: Optional[str] = None) -> 'ArxivUserClaims':
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
        if client_ipv4:
            claims['client_ipv4'] = client_ipv4
        return cls(ArxivUserClaimsModel.model_validate(claims))

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
        setattr(self._claims, tag, value)


    def encode_jwt_token(self, secret: str, algorithm: str = 'HS256') -> str:
        """packing user claims"""

        claims = self._claims.model_dump()
        # you probably forgot to add "openid" scope in Keycloak if id_token is not in it.
        # 2025-08-15 ntai: good news! I don't need to carry ID Token anymore. It was needed only for log out,
        # but I found out that you can revoke the keycloak user session with refresh token.
        del claims['acc']
        if 'idt' in claims:
            del claims['idt']
        if 'refresh' in claims:
            del claims['refresh']

        # create a NG compatible payload
        # FixMe?: This is "randomly created" in arxiv.auth.sessions.store without the shape. I gave it a shape.
        # modapi has the same shape as Auth. It would
        ng_session = NGSessionPayload(
            user_id=str(self.user_id),
            session_id=str(self.tapir_session_id),
            nonce=json.dumps(claims), # hitch the payload as nonce
            expires=self.expires_at.isoformat()
        )
        payload_ng = ng_session.model_dump()

        token = jwt.encode(payload_ng, secret, algorithm=algorithm)
        if len(token) > 4096:
            raise ValueError(f'JWT token is too long {len(token)} bytes')
        return token


    @classmethod
    def decode_jwt_payload(cls, tokens: dict, jwt_payload: str, secret: str, algorithm: str = 'HS256') -> "ArxivUserClaims":
        """
        Decodes the user claims.
        """
        payload_ng = jwt.decode(jwt_payload, secret, algorithms = [algorithm])
        try:
            payload = json.loads(payload_ng.get(NG_COOKIE_HITCHHIKER_NAME))
        except Exception as e:
            payload = {}
            pass
        tokens.update(payload)
        return cls(ArxivUserClaimsModel.model_validate(tokens))


    def update_keycloak_access_token(self, updates: dict) -> None:
        setattr(self._claims, 'acc', updates['acc'])
        return

    @property
    def domain_session(self) -> domain.Session:
        if self._domain_session is None:
            user_profile = None # domain.UserProfile()
            user = domain.User(
                username = self.username,
                email = self.email,
                user_id = self.user_id,
                name = domain.UserFullName(
                    forename = self.first_name,
                    surname = self.last_name,
                ),
                profile = user_profile,
                verified = self.email_verified,
            )
            user_scopes = scopes.GENERAL_USER
            if self.is_admin:
                user_scopes = scopes.ADMIN_USER
            authorizations = domain.Authorizations(
                classic = self.classic_capability_code,
                scopes = user_scopes,
            )
            authorizations = None

            session_id = str(self.tapir_session_id) if self.tapir_session_id else "no-session-id"
            self._domain_session = domain.Session(
                session_id = session_id,
                start_time = self.issued_at,
                user = user,
                client = None,
                end_time = None,   # The ISO-8601 datetime when the session ended.
                authorizations = authorizations, # Optional[Authorizations] = None Authorizations for the current session.
                ip_address = self.client_ip4v, # Optional[str] = None
                remote_host = None, #: Optional[str] = None
                nonce=self.kc_session_id  # : Optional[str] = None
            )
        return self._domain_session


    def set_tapir_session(self, _tapir_cookie: str, tapir_session: ArxivSession) -> None:
        self.tapir_session_id = int(tapir_session.session_id) if tapir_session.session_id else None

    pass
