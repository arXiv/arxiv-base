from ..identifier import Identifier
from ..config import settings


def pdf_canonical_url(identifier: Identifier) -> str:
    # This won't include the version unless identifier
    # was explicitly initialized with a version
    return f"https://{settings.CANONICAL_SERVER}/pdf/{identifier.idv}"


def html_canonical_url(identifier: Identifier) -> str:
    return f"https://{settings.CANONICAL_SERVER}/html/{identifier.idv}"


def abs_canonical_url(identifier: Identifier) -> str:
    return f"https://{settings.CANONICAL_SERVER}/abs/{identifier.idv}"
