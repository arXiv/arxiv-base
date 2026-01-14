"""
Acquire gcp service account auth token.
This is expected to use the default SA cred.

Make sure that the service account has the cloud run invoker role enabled if used to talk to
the service that needs auth.
"""

import typing
import datetime

import logging
from google.auth.credentials import Credentials as GcpCredentials
import google.auth.transport.requests
import google.oauth2.id_token


class GcpIdentityToken:
    _credentials: GcpCredentials
    _project: typing.Any
    _last_refresh: datetime.datetime
    target: str
    _token: str
    _logger: logging.Logger | None
    expiration: datetime.timedelta

    def __init__(
        self,
        target: str,
        logger: logging.Logger | None = None,
        expiration: datetime.timedelta = datetime.timedelta(minutes=30),
    ):
        self.expiration = expiration
        self.target = target
        self._logger = logger
        self._credentials, self._project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.refresh()
        pass

    def refresh(self) -> None:
        """Refresh the token"""
        self._last_refresh = datetime.datetime.utcnow()
        auth_req = google.auth.transport.requests.Request()
        self._token = google.oauth2.id_token.fetch_id_token(auth_req, self.target)
        if self._logger:
            self._logger.info("Token refreshed")
        pass

    @property
    def token(self) -> str:
        if datetime.datetime.utcnow() - self._last_refresh > self.expiration:
            self.refresh()
        return self._token
