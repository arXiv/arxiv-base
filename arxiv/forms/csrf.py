"""
CSRF protection for arXiv forms.

To protect a form, inherit from :class:`CSRFForm`. When the form is handled,
this class expects that:

- There is an active :class:`flask.Request`.
- The object ``flask.request.session`` exists, and has a ``str`` attribute
  ``nonce``. See :class:`arxiv.users.domain.Session` and
  :class:`arxiv.users.auth.Auth`.
- A parameter called ``CSRF_SECRET`` is set in the application configuration.

Here's an example:

.. code-block:: python


   from typing import Tuple
   from werkzeug import MultiDict
   from wtforms import StringField
   from arxiv import status
   from arxiv.forms import csrf

   ResponseData = Tuple[dict, int, dict]


   class ProtectedForm(csrf.CSRFForm):
       '''A CSRF-protected form.'''

       something_sensitive = StringField('Something sensitive')


   def some_controller(method: str, form_data: MultiDict) -> ResponseData:
       '''Handle a form-based view.'''
       headers = {}
       if method == 'POST':
           form = ProtectedForm(form_data)
           data = {'form': form}
           if not form.validate():    # Checks the CSRF token, too!
               return data, status.HTTP_400_BAD_REQUEST, headers

           # do something sensitive
           return data, status.HTTP_201_CREATED, headers

       form = ProtectedForm()
       return {'form': form}, status.HTTP_200_OK, headers


And in your template:

.. code-block:: html

   {% extends "base/base.html" %}
   {% block content %}
   <form method="POST" action="{{ url_for('ui.some_view') }}">
     {{ form.csrf_token }}
     {{ form.something_sensitive }}
     <input type="submit" class="button is-link is-small"></input>
   </form>
   {% endblock content %}

"""

import hmac
from typing import Dict, Tuple, Any
from datetime import datetime, timedelta
import dateutil.parser

from flask import request
from wtforms import Form, Field, ValidationError
from wtforms.csrf.core import CSRF
from arxiv.base.globals import get_application_config


class SessionCSRF(CSRF):
    """Session-based CSRF protection."""

    def setup_form(self, form: 'CSRFForm') -> Any:
        """Grab the CSRF context and secret from the form."""
        self.csrf_context = form.meta.csrf_context
        self.csrf_secret = form.meta.csrf_secret
        return super(SessionCSRF, self).setup_form(form)

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
                secret: str = config['CSRF_SECRET']
            except KeyError as e:
                raise RuntimeError('Parameter CSRF_SECRET must be set') from e
            return secret

        @property
        def csrf_context(self) -> Dict[str, str]:
            """Session information used to generate a CSRF token."""
            if not request or not request.session:
                raise RuntimeError('Missing active user session')

            # Sessions provided by arxiv.auth should have a nonce that was
            # generated when the session was created. Legacy sessions, however,
            # do not support this. So we'll fall back to using the session ID
            # instead.
            nonce = getattr(request.session, 'nonce',
                            request.session.session_id)
            return {
                'ip_address': request.remote_addr,
                'nonce': nonce
            }
