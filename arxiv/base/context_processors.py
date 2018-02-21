"""Context processors for the base application."""

from typing import Dict, Callable
from flask import current_app
from arxiv.base import config
from arxiv.base.exceptions import ConfigurationError


def config_url_builder() -> Dict[str, Callable]:
    """Inject a configurable URL factory."""
    def config_url(target: str) -> str:
        """Generate a URL from this app's configuration."""
        target = target.upper()
        # Look for the URL on the config of the current app (this will *not* be
        # base); fall back to the base config if not found.
        try:
            url: str = current_app.config.get(f'ARXIV_{target}_URL')
            if url is None:
                url = getattr(config, f'ARXIV_{target}_URL')
        except AttributeError as e:
            raise ConfigurationError(f'URL for {target} not set') from e
        return url
    return dict(config_url=config_url)
