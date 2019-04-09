"""Dern simple support for sending multipart/alternative e-mails."""

from typing import Optional, Dict, List
import os
from email.message import EmailMessage
from email.utils import formatdate
import smtplib

from flask import Flask, Blueprint

from arxiv.base.globals import get_application_config

NOREPLY = 'noreply@arxiv.org'


def send(recipient: str, subject: str, text_body: str,
         html_body: Optional[str] = None, sender: Optional[str] = None,
         headers: Dict[str, str] = {}, cc_recipients: List[str] = [],
         bcc_recipients: List[str] = []) -> None:
    """
    Send an e-mail.

    If both ``text_body`` and ``html_body`` are provided, the e-mail will be
    sent as ``multipart/alternative``.

    Parameters
    ----------
    recipient : str
        The e-mail address of the recipient.
    subject : str
        The subject line.
    text_body : str
        Plain text content of the e-mail.
    html_body : str
        HTML content of the e-mail.
    sender : str or None
        The e-mail address of the sender. If ``None`` (default), the default
        sender will be loaded from the current config.
    headers : dict
        Extra headers to add to the e-mail.
    cc_recipients : list
        E-mail addresses that should be CC recipients.
    bcc_recipients : list
        E-mail addresses that should be BCC recipients.

    """
    _send(_write(recipient, subject, text_body, html_body=html_body,
                 sender=sender, headers=headers, cc_recipients=cc_recipients,
                 bcc_recipients=bcc_recipients),
          host=_get_smtp_hostname(),
          port=_get_smtp_port(),
          local_hostname=_get_local_hostname(),
          username=_get_smtp_username(),
          password=_get_smtp_password(),
          use_ssl=_use_ssl())


def _write(recipient: str, subject: str, text_body: str,
           html_body: Optional[str] = None, sender: Optional[str] = None,
           headers: Dict[str, str] = {}, cc_recipients: List[str] = [],
           bcc_recipients: List[str] = []) -> EmailMessage:
    if sender is None:
        sender = _get_default_sender()
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = recipient

    # For bleeping context, see https://bugs.python.org/issue28879.
    message['Date'] = formatdate()

    if cc_recipients:
        message['CC'] = ', '.join(cc_recipients)
    if bcc_recipients:
        message['BCC'] = ', '.join(bcc_recipients)
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype='html')
    return message


def _send(message: EmailMessage, host: str = 'localhost', port: int = 0,
          local_hostname: Optional[str] = None, use_ssl: bool = False,
          username: Optional[str] = None,
          password: Optional[str] = None) -> None:
    SMTP = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with SMTP(host, port, local_hostname) as s:
        if username and password:
            s.login(username, password)
        s.send_message(message)


def _get_default_sender() -> str:
    return get_application_config().get('DEFAULT_SENDER', NOREPLY)


def _get_smtp_hostname() -> str:
    return get_application_config().get('SMTP_HOSTNAME', 'localhost')


def _get_smtp_username() -> str:
    return get_application_config().get('SMTP_USERNAME', 'foouser')


def _get_smtp_password() -> str:
    return get_application_config().get('SMTP_PASSWORD', 'foopass')


def _get_smtp_port() -> int:
    return int(get_application_config().get('SMTP_PORT', '0'))


def _get_local_hostname() -> Optional[str]:
    return get_application_config().get('SMTP_LOCAL_HOSTNAME', None)


def _use_ssl() -> bool:
    return bool(int(get_application_config().get('SMTP_SSL', '0')))


def init_app(app: Flask) -> None:
    """Configure a Flask app to use the base mail templates."""
    template_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'templates')
    blueprint = Blueprint('mail', __name__, template_folder=template_folder)
    app.register_blueprint(blueprint)
