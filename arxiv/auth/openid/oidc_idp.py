"""
OpenID connect IdP client
"""
from typing import List
import requests
import jwt
from jwt.algorithms import RSAAlgorithm, RSAPublicKey


class ArxivOidcIdpClient:
    """arXiv OpenID Connect IdP client
    This is implemented for Keycloak. If the APIs different, you may want to subclass/adjust.
    """

    server_url: str
    client_id: str
    client_secret: str | None
    realm: str
    redirect_uri: str  #
    scope: List[str]  # it's okay to be empty. Keycloak should be configured to provide scopes.
    _server_certs: dict  # Cache for the IdP certs

    def __init__(self, redirect_uri: str,
                 server_url: str = "https://openid.arxiv.org",
                 realm: str ="arxiv",
                 client_id: str = "arxiv-user",
                 scope: List[str] = [],
                 client_secret: str | None = None):
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope if scope else ["openid", "profile", "email"]
        self._server_certs = {}
        pass

    @property
    def oidc(self) -> str:
        return f'{self.server_url}/realms/{self.realm}/protocol/openid-connect'

    
    @property
    def auth_url(self) -> str:
        return self.oidc + '/auth'

    @property
    def token_url(self) -> str:
        return self.oidc + '/token'

    @property
    def certs_url(self) -> str:
        return self.oidc + '/certs'

    @property
    def login_url(self) -> str:
        scope = "&" + ",".join(self.scope) if self.scope else ""
        return f'{self.auth_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code{scope}'


    @property
    def server_certs(self) -> dict:
        if not self._server_certs:
            certs_response = requests.get(self.certs_url)
            self._server_certs = certs_response.json()
        return self._server_certs


    def get_public_key(self, kid: str) -> RSAPublicKey | None:
        for key in self.server_certs['keys']:
            if key['kid'] == kid:
                pkey = RSAAlgorithm.from_jwk(key)
                if isinstance(pkey, RSAPublicKey):
                    return pkey
        return None

    def validate_token(self, token: str) -> dict | None:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header['kid'] # key id
            algorithm = unverified_header['alg'] # key algo
            public_key = self.get_public_key(kid)
            if public_key is None:
                return None
            decoded_token: dict = jwt.decode(token, public_key, algorithms=[algorithm])
            return dict(decoded_token)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        # not reached
