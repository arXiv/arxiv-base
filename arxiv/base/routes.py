"""Provides routes for verifying base templates."""

from typing import Any, Tuple, Callable, Dict
from flask import Blueprint, render_template, current_app

from arxiv import status
from arxiv.base.exceptions import NotFound, Forbidden, Unauthorized, \
    MethodNotAllowed, RequestEntityTooLarge, BadRequest, InternalServerError

blueprint = Blueprint('ui', __name__, url_prefix='')


@blueprint.route('/test', methods=['GET'])
def test_page() -> Tuple[dict, int, dict]:
    """Render the test page."""
    return render_template("base/base.html"), status.HTTP_200_OK, {}


@blueprint.route('/404', methods=['GET'])
def test_404():
    """Test the 404 error page."""
    raise NotFound()


@blueprint.route('/403', methods=['GET'])
def test_403():
    """Test the 403 error page."""
    raise Forbidden()


@blueprint.route('/401', methods=['GET'])
def test_401():
    """Test the 401 error page."""
    raise Unauthorized()


@blueprint.route('/405', methods=['GET'])
def test_405():
    """Test the 405 error page."""
    raise MethodNotAllowed()


@blueprint.route('/413', methods=['GET'])
def test_413():
    """Test the 413 error page."""
    raise RequestEntityTooLarge()


@blueprint.route('/400', methods=['GET'])
def test_400():
    """Test the 400 error page."""
    raise BadRequest()


@blueprint.route('/500', methods=['GET'])
def test_500():
    """Test the 500 error page."""
    raise InternalServerError()
