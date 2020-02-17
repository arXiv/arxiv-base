"""
Support for typed flash alerts.

Flask provides a `simple cookie-based flashing mechanism
<http://flask.pocoo.org/docs/1.0/patterns/flashing/>`. This module extends
that mechanism to support structured alerts (i.e. dicts) and set
message categories/severity.

.. note::

   For security purposes, alerts are not treated as safe in the template by
   default. To treat a message as safe, use ``safe=True`` when generating the
   flash notification. If you use ``safe=True`` you must escape any
   user input that goes into the alert.


For example:

.. code-block:: python

   from flask import url_for
   from arxiv.base import alerts
   from jinja2 import escape

   def handle_request():
       ...

       danger_txt = request.form.somefield.value
       help_url = url_for('help')
       alerts.flash_warning(f'This is a warning, see <a href="{help_url}">'
                            f'your input {escape(danger_txt)} was not found'
                            f'the docs</a> for more information',
                            title='Warning title', safe=True)
       alerts.flash_info('This is some info', title='Info title')
       alerts.flash_failure('This is a failure', title='Failure title')
       alerts.flash_success('This is a success', title='Success title')
       alerts.flash_warning('This is a warning that cannot be dismissed',
                            dismissable=False)


:func:`flash_hidden` can be used to send hidden data across requests.

"""

from arxiv.base import logging
from typing import Optional, List, Tuple, Union
from flask import flash, Markup, get_flashed_messages

INFO = 'info'
WARNING = 'warning'
FAILURE = 'danger'   # This is odd, but we use `danger` in styles.
SUCCESS = 'success'
HIDDEN = 'hidden'

logger = logging.getLogger(__name__)


def _flash_with(severity: str, message: Union[str, dict],
                title: Optional[str] = None, dismissable: bool = True,
                safe: bool = False) -> None:
    if safe and isinstance(message, str):
        message = Markup(message)
    data = {'message': message, 'title': title, 'dismissable': dismissable}
    logger.debug('flash with severity %s: (title: %s) %s',
                 severity, title, message)
    flash(data, severity)


def flash_info(message: str, title: Optional[str] = None,
               dismissable: bool = True, safe: bool = False) -> None:
    """
    Flash an informative message to the user.

    Parameters
    ----------
    message : str
        The content of the message.
    title : str or None
        An optional title, displayed prominently atop the notification.
    dismissable : bool
        If True, a button will be provided that allows the user to hide the
        notification.
    safe : bool
        If True, the message content (only) will be treated as safe for display
        in the HTML page. NB: only use this if you know for sure that the
        message content is safe for display (i.e. you're not using raw content
        from a request).

    """
    _flash_with(INFO, message, title, dismissable, safe)


def flash_warning(message: str, title: Optional[str] = None,
                  dismissable: bool = True, safe: bool = False) -> None:
    """
    Flash a warning message to the user.

    Warnings are like info alerts, but with a higher level of concern. For
    example, this might be used to notify a user that an unintended consequence
    might be imminent.

    Parameters
    ----------
    message : str
        The content of the message.
    title : str or None
        An optional title, displayed prominently atop the notification.
    dismissable : bool
        If True, a button will be provided that allows the user to hide the
        notification.
    safe : bool
        If True, the message content (only) will be treated as safe for display
        in the HTML page. NB: only use this if you know for sure that the
        message content is safe for display (i.e. you're not using raw content
        from a request).

    """
    _flash_with(WARNING, message, title, dismissable, safe)


def flash_failure(message: str, title: Optional[str] = None,
                  dismissable: bool = True, safe: bool = False) -> None:
    """
    Flash a failure message to the user.

    Failures are an unavoidable part of life. We should be honest about our
    mistakes, and find constructive ways to move forward with our lives. That
    means that we should provide some specific hints for how the user can
    achieve success (nb: this is an important accessibility requirement).

    Parameters
    ----------
    message : str
        The content of the message.
    title : str or None
        An optional title, displayed prominently atop the notification.
    dismissable : bool
        If True, a button will be provided that allows the user to hide the
        notification.
    safe : bool
        If True, the message content (only) will be treated as safe for display
        in the HTML page. NB: only use this if you know for sure that the
        message content is safe for display (i.e. you're not using raw content
        from a request).

    """
    _flash_with(FAILURE, message, title, dismissable, safe)


def flash_success(message: str, title: Optional[str] = None,
                  dismissable: bool = True, safe: bool = False) -> None:
    """
    Flash a success message to the user.

    It's nice to know when you've done something right for a change.

    Parameters
    ----------
    message : str
        The content of the message.
    title : str or None
        An optional title, displayed prominently atop the notification.
    dismissable : bool
        If True, a button will be provided that allows the user to hide the
        notification.
    safe : bool
        If True, the message content (only) will be treated as safe for display
        in the HTML page. NB: only use this if you know for sure that the
        message content is safe for display (i.e. you're not using raw content
        from a request).

    """
    _flash_with(SUCCESS, message, title, dismissable, safe)


def flash_hidden(message: dict, key: str,
                 dismissable: bool = True, safe: bool = False) -> None:
    """
    Propagate hidden data using the flash mechanism.

    Hidden messages are not shown to the user.

    Parameters
    ----------
    message : dict
        Data to flash across requests.
    key : str or None
        Key used to identify the data.
    dismissable : bool
        If True, a button will be provided that allows the user to hide the
        notification.
    safe : bool
        If True, the message content (only) will be treated as safe for display
        in the HTML page. NB: only use this if you know for sure that the
        message content is safe for display (i.e. you're not using raw content
        from a request).

    """
    _flash_with(HIDDEN, message, key, dismissable, safe)


def get_alerts(severity: Optional[str] = None) -> List[Tuple[str, dict]]:
    """
    Get displayable alerts.

    Parameters
    ----------
    severity : str or None
        If provided (default: None), only alerts of the specified severity
        will be loaded.

    Returns
    -------
    list
        Items are (str, dict) tuples, where the first element is the severity
        and the second element is the alert itself.

    """
    alerts: List[Tuple[str, dict]]
    if severity is not None:
        alerts = get_flashed_messages(with_categories=True,
                                      category_filter=[severity])
    else:
        alerts = get_flashed_messages(with_categories=True)
    return alerts


def get_hidden_alerts(key: str) -> Optional[dict]:
    """
    Get all hidden alerts.

    Parameters
    ----------
    key : str
        Key used to generate the hidden alert in the previous request.

    Returns
    -------
    dict or None

    """
    logger.debug('all current alerts: %s', get_flashed_messages())
    logger.debug('get hidden alert "%s"', key)
    messages = get_flashed_messages(category_filter=[HIDDEN])
    logger.debug('got messages: %s', messages)
    return {m['title']: m['message'] for m in messages}.get(key, None)
