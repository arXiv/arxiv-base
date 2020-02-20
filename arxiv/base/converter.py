"""URL conversion for paths containing arXiv IDs."""

import re

from arxiv import identifier
from werkzeug.routing import BaseConverter, ValidationError


class ArXivConverter(BaseConverter):
    """Route converter for arXiv IDs."""

    def to_python(self, value: str) -> str:
        """Parse URL path part to Python rep (str)."""
        try:
            return identifier.parse_arxiv_id(value)
        except ValueError as ex:
            raise ValidationError('Not a valid arXiv ID') from ex

    def to_url(self, value: str) -> str:
        """Cast Python rep (str) to URL path part."""
        return value
