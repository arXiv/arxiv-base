"""Provides routes for verifying base templates."""

from typing import Any, Tuple, Callable, Dict
from flask import Blueprint, render_template, current_app

from arxiv import status

blueprint = Blueprint('ui', __name__, url_prefix='')


@blueprint.route('/test', methods=['GET'])
def test_page() -> Tuple[dict, int, dict]:
    """Render the test page."""
    return render_template("base/base.html"), status.HTTP_200_OK, {}
