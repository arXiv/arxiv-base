"""CSRF protection for arXiv forms.

DO NOT USE THIS PACKAGE.

This package is flawed and not currently used in production. It
assumes the client will respond on the same IP address that it used to
request the form.

Look at the wtforms CSRF docs and use the examples there.
"""
import warnings

import hmac
from typing import Dict, Tuple, Any
from datetime import datetime, timedelta
import dateutil.parser

from flask import request
from wtforms import Form, Field, ValidationError
from wtforms.csrf.core import CSRF
from arxiv.base.globals import get_application_config

warnings.warn("Deprecated: Do not use. each package should use WTForms CSRF as needed", DeprecationWarning)

class SessionCSRF(CSRF):
    """Session-based CSRF protection."""

    def setup_form(self, form: 'CSRFForm') -> Any:
        """Grab the CSRF context and secret from the form."""
        warnings.warn("Deprecated: Do not use.", DeprecationWarning)

        self.csrf_context = form.meta.csrf_context
        self.csrf_secret = form.meta.csrf_secret
        self.csrf_timeout = form.meta.csrf_timeout
        return super(SessionCSRF, self).setup_form(form)

    @staticmethod
    def _hash(secret: str, nonce: str, ip_address: str, expires: str) -> str:
        ctx = f"{nonce}{ip_address}{expires}".encode('utf-8')
        csrf_hmac = hmac.new(secret.encode('utf-8'), ctx, digestmod='sha256')
        return csrf_hmac.hexdigest()

    @staticmethod
    def _new_expiry(timeout: int) -> str:
        if timeout:
            return (datetime.now() + timedelta(seconds=timeout)).isoformat()
        else:
            return "never"

    @staticmethod
    def _join(digest: str, expires: str) -> str:
        return f"{digest}::{expires}"

    @staticmethod
    def _split(csrf_token: str) -> Tuple[str, str]:
        digest, expires = csrf_token.split('::', 1)
        return digest, expires

    def generate_csrf_token(self, field: 'CSRFForm') -> str:
        """Generate a new CSRF token using the CSRF secret and context."""
        expires = self._new_expiry(self.csrf_timeout)
        nonce = self.csrf_context['nonce']
        ip_address = self.csrf_context['ip_address']
        digest = self._hash(self.csrf_secret, nonce, ip_address, expires)
        return self._join(digest, expires)

    def validate_csrf_token(self, form: 'CSRFForm', field: Field) -> None:
        """Validate the CSRF token passed with form data."""
        if field.data is None:
            raise ValidationError('Missing CSRF token')
        digest, expires = self._split(field.data)
        nonce = self.csrf_context['nonce']
        ip_address = self.csrf_context['ip_address']
        expected = self._hash(self.csrf_secret, nonce, ip_address, expires)
        if self.csrf_timeout and \
                dateutil.parser.parse(expires) <= datetime.now():
            raise ValidationError('CSRF token has expired')
        if not hmac.compare_digest(expected, digest):
            raise ValidationError('CSRF token is invalid')


class CSRFForm(Form):
    """Base form with support for CSRF protection."""

    class Meta:
        """Set CSRF configuration."""

        csrf = True
        csrf_field_name = "csrf_token"
        csrf_class = SessionCSRF    # Set the CSRF implementation
        csrf_timeout = 30 * 60  # seconds

        @property
        def csrf_secret(self) -> str:
            """CSRF secret from the current application configuration."""
            config = get_application_config()
            try:
                secret: str = config['CSRF_SECRET']
            except KeyError as ex:
                raise RuntimeError('Parameter CSRF_SECRET must be set') from ex
            return secret

        @property
        def csrf_context(self) -> Dict[str, str]:
            """Session information used to generate a CSRF token."""
            if not request or (not hasattr(request, 'session')
                               and not hasattr(request, 'auth')):
                raise RuntimeError('Missing active user session')

            # Per ARXIVNG-1944 in arxiv-auth v0.4.1 the session will be called
            # request.auth by default.
            session = getattr(request, 'auth') or getattr(request, 'session')

            # Sessions provided by arxiv.auth should have a nonce that was
            # generated when the session was created. Legacy sessions, however,
            # do not support this. So we'll fall back to using the session ID
            # instead.
            nonce = getattr(session, 'nonce', session.session_id)
            return {
                'ip_address': getattr(request, 'remote_addr'),
                'nonce': nonce
            }
