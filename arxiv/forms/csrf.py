"""
CSRF protection for arXiv forms.

To protect a form, inherit from :class:`CSRFForm`. When the form is handled,
this class expects that:

- There is an active :class:`flask.Request`.
- The object ``flask.request.session`` exists, and has a ``str`` attribute
  ``nonce``. See :class:`arxiv.users.domain.Session` and
  :class:`arxiv.users.auth.Auth`.
- A parameter called ``CSRF_SECRET`` is set in the application configuration.


"""

import hmac
from typing import Dict, Tuple
from datetime import datetime, timedelta
import dateutil.parser

from flask import request
from wtforms import Form, Field, ValidationError
from wtforms.csrf.core import CSRF
from arxiv.base.globals import get_application_config


class SessionCSRF(CSRF):
    """Session-based CSRF protection."""

    def setup_form(self, form: 'CSRFForm') -> None:
        """Grab the CSRF context and secret from the form."""
        self.csrf_context = form.meta.csrf_context
        self.csrf_secret = form.meta.csrf_secret
        super(SessionCSRF, self).setup_form(form)

    @staticmethod
    def _hash(secret: str, nonce: str, ip_address: str, expires: str) -> str:
        ctx = f"{nonce}{ip_address}{expires}".encode('utf-8')
        csrf_hmac = hmac.new(secret.encode('utf-8'), ctx, digestmod='sha256')
        return csrf_hmac.hexdigest()

    @staticmethod
    def _new_expiry() -> str:
        return (datetime.now() + timedelta(seconds=300)).isoformat()

    @staticmethod
    def _join(digest: str, expires: str) -> str:
        return f"{digest}::{expires}"

    @staticmethod
    def _split(csrf_token: str) -> Tuple[str, str]:
        digest, expires = csrf_token.split('::', 1)
        return digest, expires

    def generate_csrf_token(self, field: 'CSRFForm') -> str:
        """Generate a new CSRF token using the CSRF secret and context."""
        expires = self._new_expiry()
        nonce = self.csrf_context['nonce']
        ip_address = self.csrf_context['ip_address']
        digest = self._hash(self.csrf_secret, nonce, ip_address, expires)
        return self._join(digest, expires)

    def validate_csrf_token(self, form: 'CSRFForm', field: Field) -> None:
        """Validate the CSRF token passed with form data."""
        digest, expires = self._split(field.data)
        nonce = self.csrf_context['nonce']
        ip_address = self.csrf_context['ip_address']
        expected = self._hash(self.csrf_secret, nonce, ip_address, expires)
        if dateutil.parser.parse(expires) <= datetime.now():
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

        @property
        def csrf_secret(self) -> str:
            """The CSRF secret from the current application configuration."""
            config = get_application_config()
            try:
                secret: str = config.get['CSRF_SECRET']
            except KeyError as e:
                raise RuntimeError('Parameter CSRF_SECRET must be set') from e
            return secret

        @property
        def csrf_context(self) -> Dict[str, str]:
            """Session information used to generate a CSRF token."""
            if not hasattr(request, 'session') \
                    or not hasattr(request.session, 'nonce'):
                raise RuntimeError('Missing active user session or nonce')

            return {
                'ip_address': request.remote_addr,
                'nonce': request.session.nonce
            }
