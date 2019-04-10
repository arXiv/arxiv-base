"""
Provides routes for verifying base templates and exception handling.

The blueprint instantiated here is **not** for use in a production application;
it is not attached by :class:`arxiv.base.Base`.
"""

from typing import Any, Tuple, Callable, Dict
from datetime import datetime
from flask import Blueprint, render_template, current_app, make_response, \
    Response, flash, url_for

from http import HTTPStatus as status
from arxiv.base.exceptions import NotFound, Forbidden, Unauthorized, \
    MethodNotAllowed, RequestEntityTooLarge, BadRequest, InternalServerError

from . import alerts

blueprint = Blueprint('ui', __name__, url_prefix='',
                      static_folder='./static_test')


@blueprint.route('/styleguide', methods=['GET'])
def test_page() -> Response:
    """Render the test page."""
    rendered = render_template("base/styleguide.html", pagetitle='Home')
    response: Response = make_response(rendered, status.OK)

    # Demonstrate flash alerts. To see these alerts, reload the page.
    help_url = url_for('help')
    alerts.flash_warning(f'This is a warning, see <a href="{help_url}">the'
                         f' docs</a> for more information',
                         title='Warning title', safe=True)
    alerts.flash_info('This is some info', title='Info title')
    alerts.flash_failure('This is a failure', title='Failure title')
    alerts.flash_success('This is a success', title='Success title')
    alerts.flash_warning('This is a warning that cannot be dismissed',
                           dismissable=False)
    return response


@blueprint.route('/macros', methods=['GET'])
def test_macros() -> Response:
    """Test the template macros."""
    context = {
        'arxiv_id': 'physics/9707012',
        'title': 'Supersymmetric partner chirping of Newtonian free damping',
        'authors': 'H.C. Rosu, J.L. Romero, J. Socorro',
        'abstract': "We connect the classical free damping cases by means of"
                    " Rosner's construction in supersymmetric quantum"
                    " mechanics. Starting with the critical damping, one"
                    " can obtain in the underdamping case a chirping of"
                    " instantaneous physical frequency $\omega ^{2}(t) \propto"
                    " \omega_{u}^{2}sech^2(\omega_{u}t)$, whereas in the"
                    " overdamped case the \"chirping\" is of the (unphysical)"
                    " type $\omega ^{2}(t)\propto\omega_{o}^{2}sec^{2}(\omega_"
                    "{o}t)$, where $\omega_{u}$ and $\omega_{o}$ are the"
                    " underdamped and overdamped frequency parameters,"
                    " respectively.\n This has an \"abstract\" linefeed.""",
        'comments': "This version (physics/9707012v2) was not stored by arXiv."
                    " A subsequent replacement was made before versioning was"
                    " introduced.",
        'primary_category': 'cond-mat.supr-con',
        'submitted_date': datetime.now(),
        'submission_history': [
            {'version': 1, 'submitted_date': datetime.now()},
            {'version': 2, 'submitted_date': datetime.now()},
            {'version': 3, 'submitted_date': datetime.now()},
        ],
        'version': 2,
        'doi': '10.1000/182',
        'pagetitle': 'Home'
    }
    response: Response = render_template("base/testmacros.html", **context)
    return response


@blueprint.route('/404', methods=['GET'])
def test_404() -> Response:
    """Test the 404 error page."""
    raise NotFound()


@blueprint.route('/403', methods=['GET'])
def test_403() -> Response:
    """Test the 403 error page."""
    raise Forbidden()


@blueprint.route('/401', methods=['GET'])
def test_401() -> Response:
    """Test the 401 error page."""
    raise Unauthorized()


@blueprint.route('/405', methods=['GET'])
def test_405() -> Response:
    """Test the 405 error page."""
    raise MethodNotAllowed()


@blueprint.route('/413', methods=['GET'])
def test_413() -> Response:
    """Test the 413 error page."""
    raise RequestEntityTooLarge()


@blueprint.route('/400', methods=['GET'])
def test_400() -> Response:
    """Test the 400 error page."""
    raise BadRequest()


@blueprint.route('/500', methods=['GET'])
def test_500() -> Response:
    """Test the 500 error page."""
    raise InternalServerError()
