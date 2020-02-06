"""Tests for :mod:`arxiv.forms`."""

from unittest import TestCase, mock
from datetime import datetime
from werkzeug.datastructures import MultiDict
from wtforms import StringField
from . import csrf


class TestCSRFForm(TestCase):
    """Tests for :class:`arxiv.forms.csrf.CSRFForm`."""

    @mock.patch(f"{csrf.__name__}.request")
    @mock.patch(f"{csrf.__name__}.get_application_config")
    def test_invalid_token(self, mock_get_config, mock_request):
        """An invalid CSRF token is passed in the form data."""
        mock_request.remote_addr = "10.10.10.10"
        mock_request.auth = None
        mock_request.session = mock.MagicMock(nonce="foononce123")
        mock_get_config.return_value = {"CSRF_SECRET": "foosecret"}

        class ProtectedForm(csrf.CSRFForm):
            """A CSRF-protected form."""

            something_sensitive = StringField("Something sensitive")

        data = MultiDict({"something_sensitive": "foo", "csrf_token": "nope"})
        form = ProtectedForm(data)
        self.assertFalse(form.validate(), "The form is not valid")

    @mock.patch(f"{csrf.__name__}.request")
    @mock.patch(f"{csrf.__name__}.get_application_config")
    def test_valid_token(self, mock_get_config, mock_request):
        """A valid CSRF token is passed in the form data."""
        ip_address = "10.10.10.10"
        nonce = "foononce123"
        secret = "foosecret"
        mock_request.remote_addr = ip_address
        mock_request.auth = None
        mock_request.session = mock.MagicMock(nonce=nonce)
        mock_get_config.return_value = {"CSRF_SECRET": secret}

        class ProtectedForm(csrf.CSRFForm):
            """A CSRF-protected form."""

            something_sensitive = StringField("Something sensitive")

        form = ProtectedForm()

        expires = csrf.SessionCSRF._new_expiry(form.meta.csrf_timeout)
        digest = csrf.SessionCSRF._hash(secret, nonce, ip_address, expires)
        csrf_token = csrf.SessionCSRF._join(digest, expires)

        data = MultiDict({"something_sensitive": "foo", "csrf_token": csrf_token})
        form = ProtectedForm(data)
        self.assertTrue(form.validate(), "The form is valid")

    @mock.patch(f"{csrf.__name__}.request")
    @mock.patch(f"{csrf.__name__}.get_application_config")
    def test_expired_token(self, mock_get_config, mock_request):
        """A valid but expired CSRF token is passed in the form data."""
        ip_address = "10.10.10.10"
        nonce = "foononce123"
        secret = "foosecret"
        expires = datetime.now().isoformat()
        digest = csrf.SessionCSRF._hash(secret, nonce, ip_address, expires)
        csrf_token = csrf.SessionCSRF._join(digest, expires)

        mock_request.remote_addr = ip_address
        mock_request.auth = None
        mock_request.session = mock.MagicMock(nonce=nonce)
        mock_get_config.return_value = {"CSRF_SECRET": secret}

        class ProtectedForm(csrf.CSRFForm):
            """A CSRF-protected form."""

            something_sensitive = StringField("Something sensitive")

        data = MultiDict({"something_sensitive": "foo", "csrf_token": csrf_token})
        form = ProtectedForm(data)
        self.assertFalse(form.validate(), "The form is not valid")


class TestCSRFFormWithNewSessionRef(TestCase):
    """Test using the ``request.auth`` session ref in accounts v0.4.1."""

    @mock.patch(f"{csrf.__name__}.request")
    @mock.patch(f"{csrf.__name__}.get_application_config")
    def test_invalid_token(self, mock_get_config, mock_request):
        """An invalid CSRF token is passed in the form data."""
        mock_request.remote_addr = "10.10.10.10"
        mock_request.session = None
        mock_request.auth = mock.MagicMock(nonce="foononce123")
        mock_get_config.return_value = {"CSRF_SECRET": "foosecret"}

        class ProtectedForm(csrf.CSRFForm):
            """A CSRF-protected form."""

            something_sensitive = StringField("Something sensitive")

        data = MultiDict({"something_sensitive": "foo", "csrf_token": "nope"})
        form = ProtectedForm(data)
        self.assertFalse(form.validate(), "The form is not valid")

    @mock.patch(f"{csrf.__name__}.request")
    @mock.patch(f"{csrf.__name__}.get_application_config")
    def test_valid_token(self, mock_get_config, mock_request):
        """A valid CSRF token is passed in the form data."""
        ip_address = "10.10.10.10"
        nonce = "foononce123"
        secret = "foosecret"
        mock_request.remote_addr = ip_address
        mock_request.session = None
        mock_request.auth = mock.MagicMock(nonce=nonce)
        mock_get_config.return_value = {"CSRF_SECRET": secret}

        class ProtectedForm(csrf.CSRFForm):
            """A CSRF-protected form."""

            something_sensitive = StringField("Something sensitive")

        form = ProtectedForm()

        expires = csrf.SessionCSRF._new_expiry(form.meta.csrf_timeout)
        digest = csrf.SessionCSRF._hash(secret, nonce, ip_address, expires)
        csrf_token = csrf.SessionCSRF._join(digest, expires)

        data = MultiDict({"something_sensitive": "foo", "csrf_token": csrf_token})
        form = ProtectedForm(data)
        self.assertTrue(form.validate(), "The form is valid")

    @mock.patch(f"{csrf.__name__}.request")
    @mock.patch(f"{csrf.__name__}.get_application_config")
    def test_expired_token(self, mock_get_config, mock_request):
        """A valid but expired CSRF token is passed in the form data."""
        ip_address = "10.10.10.10"
        nonce = "foononce123"
        secret = "foosecret"
        expires = datetime.now().isoformat()
        digest = csrf.SessionCSRF._hash(secret, nonce, ip_address, expires)
        csrf_token = csrf.SessionCSRF._join(digest, expires)

        mock_request.remote_addr = ip_address
        mock_request.session = None
        mock_request.auth = mock.MagicMock(nonce=nonce)
        mock_get_config.return_value = {"CSRF_SECRET": secret}

        class ProtectedForm(csrf.CSRFForm):
            """A CSRF-protected form."""

            something_sensitive = StringField("Something sensitive")

        data = MultiDict({"something_sensitive": "foo", "csrf_token": csrf_token})
        form = ProtectedForm(data)
        self.assertFalse(form.validate(), "The form is not valid")
