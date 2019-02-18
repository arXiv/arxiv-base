from typing import Optional, Dict, List
from email.message import EmailMessage
import smtplib
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
                 bcc_recipients=bcc_recipients))


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
    if cc_recipients:
        message['CC'] = ', '.join(cc_recipients)
    if bcc_recipients:
        message['BCC'] = ', '.join(bcc_recipients)
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype='html')
    return message


def _send(message: EmailMessage, host: str = 'localhost', port: int = 0,
          local_hostname: Optional[str] = None) -> None:
    with smtplib.SMTP(host, port, local_hostname) as s:
        s.send_message(message)


def _get_default_sender() -> str:
    return get_application_config().get('DEFAULT_SENDER', NOREPLY)
