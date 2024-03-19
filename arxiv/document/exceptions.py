class AbsException(Exception):
    """Error class for general arXiv .abs exceptions."""


class AbsNotFoundException(FileNotFoundError, AbsException):
    """Error class for arXiv .abs file not found exceptions."""


class AbsVersionNotFoundException(FileNotFoundError, AbsException):
    """Error class for arXiv .abs file version not found exceptions."""


class AbsParsingException(OSError, AbsException):
    """Error class for arXiv .abs file parsing exceptions."""


class AbsDeletedException(AbsException):
    """Error class for arXiv papers that have been deleted."""
