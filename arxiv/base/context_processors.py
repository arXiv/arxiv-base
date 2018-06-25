"""Context processors for the base application."""

from typing import Dict, Callable
from arxiv.base.urls import config_url


def config_url_builder() -> Dict[str, Callable]:
    """Inject :func:`.config_url` into the template rendering context."""
    return dict(config_url=config_url)
