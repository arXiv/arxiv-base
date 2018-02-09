"""Provides routes for verifying base templates."""

from typing import Any, Tuple, Callable, Dict
from flask import Blueprint, render_template, current_app

from arxiv import status

blueprint = Blueprint('ui', __name__, url_prefix='')


@blueprint.route('/test', methods=['GET'])
def test_page() -> Tuple[dict, int, dict]:
    """Render the test page."""
    return render_template("base/base.html"), status.HTTP_200_OK, {}


@blueprint.context_processor
def config_url_builder() -> Dict[str, Callable]:
    """Inject a configurable URL factory."""
    def config_url(target: str) -> str:
        """Generate a URL from this app's configuration."""
        target = target.upper()
        # Will raise a KeyError; that seems reasonable?
        url: str = current_app.config[f'ARXIV_{target}_URL']
        return url
    return dict(config_url=config_url)
