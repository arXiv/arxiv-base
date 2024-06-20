"""Exceptions for legacy user/session integration."""


class AuthenticationFailed(RuntimeError):
    """Failed to authenticate user with provided credentials."""


class NoSuchUser(RuntimeError):
    """A reference to a non-existant user was passed."""


class PasswordAuthenticationFailed(RuntimeError):
    """An invalid username/password combination were provided."""


class SessionCreationFailed(RuntimeError):
    """Failed to create a session in the legacy database."""


class SessionDeletionFailed(RuntimeError):
    """Failed to delete a session in the legacy database."""


class UnknownSession(RuntimeError):
    """Failed to locate a session in the legacy database."""


class SessionExpired(RuntimeError):
    """A reference was made to an expired session."""


class InvalidCookie(ValueError):
    """The value of a passed legacy cookie is not valid."""


class RegistrationFailed(RuntimeError):
    """Could not create a new user."""


class UpdateUserFailed(RuntimeError):
    """Could not update a user."""


class Unavailable(RuntimeError):
    """The database is temporarily unavailable."""
