class AbsException(Exception):
    """Error class for general arXiv .abs exceptions."""


class AbsNotFoundException(FileNotFoundError):
    """Error class for arXiv .abs file not found exceptions."""


class AbsVersionNotFoundException(FileNotFoundError):
    """Error class for arXiv .abs file version not found exceptions."""


class AbsParsingException(OSError):
    """Error class for arXiv .abs file parsing exceptions."""


class AbsDeletedException(Exception):
    """Error class for arXiv papers that have been deleted."""
