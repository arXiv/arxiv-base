"""Exceptions for legacy user/session integration."""

class ArxivAuthException(RuntimeError):
    """Super class for all auth errors."""

class AuthenticationFailed(ArxivAuthException):
    """Failed to authenticate user with provided credentials."""


class NoSuchUser(ArxivAuthException):
    """A reference to a non-existant user was passed."""


class PasswordAuthenticationFailed(ArxivAuthException):
    """An invalid username/password combination were provided."""


class SessionCreationFailed(ArxivAuthException):
    """Failed to create a session in the legacy database."""


class SessionDeletionFailed(ArxivAuthException):
    """Failed to delete a session in the legacy database."""


class UnknownSession(ArxivAuthException):
    """Failed to locate a session in the legacy database."""


class SessionExpired(ArxivAuthException):
    """A reference was made to an expired session."""


class InvalidCookie(ArxivAuthException):
    """The value of a passed legacy cookie is not valid."""


class RegistrationFailed(ArxivAuthException):
    """Could not create a new user."""


class UpdateUserFailed(ArxivAuthException):
    """Could not update a user."""