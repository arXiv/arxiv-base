"""URL conversion for paths containing arXiv IDs."""

import re

from arxiv import identifier
from werkzeug.routing import BaseConverter, ValidationError


class ArXivConverter(BaseConverter):
    """Route converter for arXiv IDs."""

    def to_python(self, value: str) -> str:
        """Parse URL path part to Python rep (str)."""
        return identifier.parse_arxiv_id(value)

    def to_url(self, value: str) -> str:
        """Cast Python rep (str) to URL path part."""
        return value
