"""Exceptions for HTTP integrations."""

from requests import Response


class RequestFailed(IOError):
    """The file management service returned an unexpected status code."""

    def __init__(self, msg: str, response: Response) -> None:
        """Attach (optional) data to the exception."""
        self.response = response
        super(RequestFailed, self).__init__(msg)

    @property
    def status_code(self) -> int:
        """Get the code from the response originating the exception."""
        return self.response.status_code


class RequestUnauthorized(RequestFailed):
    """Client/user is not authenticated."""


class RequestForbidden(RequestFailed):
    """Client/user is not allowed to perform this request."""


class BadRequest(RequestFailed):
    """The request was malformed or otherwise improper."""


class Oversize(BadRequest):
    """The upload was too large."""


class NotFound(BadRequest):
    """The referenced upload does not exist."""


class BadResponse(RequestFailed):
    """The response from the file management service was malformed."""


class ConnectionFailed(IOError):
    """Could not connect to the file management service."""


class SecurityException(ConnectionFailed):
    """Raised when SSL connection fails."""
