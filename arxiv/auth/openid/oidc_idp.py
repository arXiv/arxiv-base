"""
OpenID connect IdP client
"""

import json
from datetime import datetime
from typing import List, Any
import requests
from requests.auth import HTTPBasicAuth
import jwt
from jwt.algorithms import RSAAlgorithm, RSAPublicKey

from arxiv.base import logging

from ..user_claims import ArxivUserClaims


class ArxivOidcIdpClient:
    """arXiv OpenID Connect IdP client
    This is implemented for Keycloak at the moment.
    If the APIs different, you may want to refactor for supreclass/subclass/adjust.
    """

    server_url: str
    client_id: str
    client_secret: str | None
    realm: str
    redirect_uri: str  #
    scope: List[str]  # it's okay to be empty. Keycloak should be configured to provide scopes.
    _server_certs: dict  # Cache for the IdP certs
    _logger: logging.Logger

    def __init__(self, redirect_uri: str,
                 server_url: str = "https://openid.arxiv.org",
                 realm: str = "arxiv",
                 client_id: str = "arxiv-user",
                 scope: List[str] | None = None,
                 client_secret: str | None = None,
                 login_url: str | None = None,
                 logger: logging.Logger | None = None,
                 ):
        """
        Make Tapir user data from pass-data

        Parameters
        ----------
        redirect_uri: Callback URL - typically  FOO/callback which is POSTED when the IdP
            authentication succeeds.
        server_url: IdP's URL
        realm: OpenID's realm - for arXiv users, it should be "arxiv"
        client_id: Registered client ID. OAuth2 client/callback are registered on IdP and need to
            match
        scope: List of OAuth2 scopes
        client_secret: Registered client secret
        login_url: redircet URL when not logged in or logged out
        logger: Python logging logger instance
        """
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope if scope else ["openid", "basic", "profile", "email", "userid", "roles",
                                          "microprofile-jwt"]
        self.login_url = login_url
        self._server_certs = {}
        self._logger = logger or logging.getLogger(__name__)
        pass

    @property
    def oidc(self) -> str:
        return f'{self.server_url}/realms/{self.realm}/protocol/openid-connect'

    @property
    def auth_url(self) -> str:
        return self.oidc + '/auth'

    @property
    def token_url(self) -> str:
        """https://openid.net/specs/openid-connect-core-1_0.html#TokenEndpoint"""
        return self.oidc + '/token'

    @property
    def token_introspect_url(self) -> str:
        return self.oidc + '/token/introspect'

    @property
    def certs_url(self) -> str:
        return self.oidc + '/certs'

    @property
    def user_info_url(self) -> str:
        return self.oidc + '/userinfo'

    def logout_url(self, user: ArxivUserClaims, url: str | None = None) -> str:
        url = self.login_url if url is None else url
        return self.oidc + f'/logout?id_token_hint={user.id_token}' if url is None else f'&post_logout_redirect_uri={url}'

    @property
    def login_url(self) -> str:
        scope = "&" + ",".join(self.scope) if self.scope else ""
        return f'{self.auth_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code{scope}'

    @property
    def server_certs(self) -> dict:
        """Get IdP server's SSL certificates"""
        # I'm having some 2nd thought about caching this. Fresh cert every time is probably needed
        # if not self._server_certs:
        # This adds one extra fetch but it avoids weird expired certs situation
        certs_response = requests.get(self.certs_url)
        self._server_certs = certs_response.json()
        return self._server_certs

    def get_public_key(self, kid: str) -> RSAPublicKey | None:
        """
        Find the public key for the given key
        """
        for key in self.server_certs['keys']:
            if key['kid'] == kid:
                pkey = RSAAlgorithm.from_jwk(key)
                if isinstance(pkey, RSAPublicKey):
                    return pkey
        return None

    def acquire_idp_token(self, code: str) -> dict | None:
        """With the callback's code, go get the access token from IdP.

        Parameters
        ----------
        code: When IdP calls back, it comes with the authentication code as a query parameter.
        """
        auth = None
        if self.client_secret:
            try:
                auth = HTTPBasicAuth(self.client_id, self.client_secret)
                self._logger.debug(f'client auth success')
            except requests.exceptions.RequestException:
                self._logger.debug(f'client auth failed')
                return None
            except Exception as exc:
                self._logger.warning(f'client auth failed', exc_info=True)
                raise

        try:
            # Exchange the authorization code for an access token
            token_response = requests.post(
                self.token_url,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self.redirect_uri,
                    'client_id': self.client_id,
                },
                auth=auth
            )
            if token_response.status_code != 200:
                # need logging here
                self._logger.warning(f'idp %s', token_response.status_code)
                return None
            # returned data should be
            # https://openid.net/specs/openid-connect-core-1_0.html#TokenResponse
            return token_response.json()
        except requests.exceptions.RequestException:
            return None

    def validate_access_token(self, access_token: str) -> dict | None:
        """
        Given the IdP's access token, validate it and unpack the token payload. This should
        comply to OpenID standard, hopefully.

        Parameters
        ----------
        access_token: This is the access token in the IdP's token that you get from the code

        Return
        ------
        None -> Invalid access token
        dict -> The content of idp token as dict
        """

        try:
            unverified_header = jwt.get_unverified_header(access_token)
            kid = unverified_header['kid']  # key id
            algorithm = unverified_header['alg']  # key algo
            public_key = self.get_public_key(kid)
            if public_key is None:
                self._logger.info("Validating the token failed. kid=%s alg=%s", kid, algorithm)
                return None
            decoded_token: dict = jwt.decode(access_token, public_key, algorithms=[algorithm])
            return dict(decoded_token)
        except jwt.ExpiredSignatureError:
            self._logger.warning("IdP signature cert is expired.")
            return None
        except jwt.InvalidTokenError:
            self._logger.warning("Token is invalid.")
            return None
        # not reached

    def to_arxiv_user_claims(self, idp_claims: dict, access_token: str,
                             refresh_token: str) -> ArxivUserClaims:
        """
        Given the IdP's access token claims, make Arxiv user claims.

        NOTE: As you can see, this is made for keycloak. If we use a different IdP, you want
        to override this.

        Parameters
        ----------
        idp_claims: This is the contents of (unpacked) access token. IdP signs it with the private
            key, and the value is verified using the published public cert.
        access_token: The original access token
        refresh_token: The original refresh token
        """
        claims = ArxivUserClaims.from_keycloak_claims(idp_claims, access_token, refresh_token)
        return claims

    def from_code_to_user_claims(self, code: str) -> ArxivUserClaims | None:
        """
        Put it all together

        When you get the /callback with the code that the IdP returned, go get the access token,
        validate it, and then turn it to ArxivUserClaims
        user_claims.to_arxiv_token_string, idp_token=idp_token

        Parameters
        ----------
        code: The code you get in the /callback

        Returns
        -------
        ArxivUserClaims: User's IdP claims
        None: Something is wrong

        Note
        ----
        When something goes wrong, generally, it is "invisible" from the user's point of view.
        At the moment, only way to figure this out is to look at the logging.

        Generally speaking, when /callback gets the auth code, the rest should work. Only time this
        isn't the case is something is wrong with IdP server, network issue, or bug in the code.
        """
        idp_token = self.acquire_idp_token(code)
        if not idp_token:
            return None
        access_token = idp_token.get('access_token')  # oauth 2 access token
        if not access_token:
            return None
        idp_claims = self.validate_access_token(access_token)
        if not idp_claims:
            return None
        return self.to_arxiv_user_claims(idp_claims, access_token, idp_token.get('refresh_token'))

    def logout_user(self, user: ArxivUserClaims) -> bool:
        """With user's access token, logout user.

        Parameters
        ----------
        user: ArxivUserClaims
        """
        try:
            header = {
                "Authorization": f"Bearer {user.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        except KeyError:
            return None

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        url = self.logout_url(user)
        try:
            response = requests.post(url, headers=header, data=data, timeout=10)
            if response.status_code == 200:
                self._logger.warning(
                    "Keycloak is misconfigured. Turn front channel logout off in the logout settings of the client.")
            self._logger.info("Uesr %s logged out.", user.username)
            return response.status_code == 204
        except requests.exceptions.RequestException:
            self._logger.error("Failed to connect to %s", url)
            return False
