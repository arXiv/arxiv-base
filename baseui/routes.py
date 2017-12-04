"""Provides routes for verifying baseui templates."""

from flask import Blueprint, render_template

blueprint = Blueprint('ui', __name__, url_prefix='')


@blueprint.route('/test', methods=['GET'])
def test_page() -> tuple:
    """Render the test page."""
    return render_template("baseui/base.html")
