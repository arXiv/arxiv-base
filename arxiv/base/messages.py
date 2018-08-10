"""
Support for typed flash messages.

Flask provides a `simple cookie-based flashing mechanism
<http://flask.pocoo.org/docs/1.0/patterns/flashing/>`. This module extends
that mechanism to support structured messages (i.e. dicts) and set
message categories/severity.

.. note::

   For security purposes, messages are not treated as safe in the template by
   default. To treat a message as safe, use ``safe=True`` when generating the
   flash notification.


For example:

.. code-block:: python

   from flask import url_for
   from arxiv.base import messages

   def handle_request():
       ...

       help_url = url_for('help')
       messages.flash_warning(f'This is a warning, see <a href="{help_url}">'
                              f'the docs</a> for more information',
                              title='Warning title', safe=True)
       messages.flash_info('This is some info', title='Info title')
       messages.flash_failure('This is a failure', title='Failure title')
       messages.flash_success('This is a success', title='Success title')
       messages.flash_warning('This is a warning that cannot be dismissed',
                              dismissable=False)

"""

from typing import Optional
from flask import flash, Markup

INFO = 'info'
WARNING = 'warning'
FAILURE = 'danger'   # This is odd, but we use `danger` in styles.
SUCCESS = 'success'


def _flash_with(severity: str, message: str, title: Optional[str] = None,
                dismissable: bool = True, safe: bool = False) -> None:
    if safe:
        message = Markup(message)
    data = {'message': message, 'title': title, 'dismissable': dismissable}
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

    Warnings are like info messages, but with a higher level of concern. For
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
