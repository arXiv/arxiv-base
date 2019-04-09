"""Test sending email."""

from unittest import TestCase, mock
from .. import mail


class TestSendEmail(TestCase):
    """Tests for :func:`mail.send`."""

    @mock.patch(f'{mail.__name__}.smtplib.SMTP')
    def test_send_text(self, mock_SMTP):
        """Send a text-only e-mail."""
        mock_SMTP_instance = mock.MagicMock()
        mock_SMTP.return_value.__enter__.return_value = mock_SMTP_instance
        mail.send("erick.peirson@gmail.com", "Subject!", "Hi there.")
        expected = [
            'Subject: Subject!',
            'From: noreply@arxiv.org',
            'To: erick.peirson@gmail.com',
            'Content-Type: text/plain; charset="utf-8"',
            'Content-Transfer-Encoding: 7bit',
            'MIME-Version: 1.0',
            'Hi there.',
        ]
        content = str(mock_SMTP_instance.send_message.call_args[0][0])
        for part in expected:
            self.assertIn(part, content)

    @mock.patch(f'{mail.__name__}.smtplib.SMTP')
    def test_send_text_with_cc_and_bcc(self, mock_SMTP):
        """Send a text-only e-mail with CC and BCC recipients."""
        mock_SMTP_instance = mock.MagicMock()
        mock_SMTP.return_value.__enter__.return_value = mock_SMTP_instance
        mail.send("erick.peirson@gmail.com", "Subject!", "Hi there.",
                  cc_recipients=['foo@somewhere.edu', 'baz@somewhere.edu'],
                  bcc_recipients=['bar@elsewhere.edu'])
        expected = [
            'Subject: Subject!',
            'From: noreply@arxiv.org',
            'To: erick.peirson@gmail.com',
            'CC: foo@somewhere.edu, baz@somewhere.edu',
            'BCC: bar@elsewhere.edu',
            'Content-Type: text/plain; charset="utf-8"',
            'Content-Transfer-Encoding: 7bit',
            'MIME-Version: 1.0',
            'Hi there.',
        ]
        content = str(mock_SMTP_instance.send_message.call_args[0][0])
        for part in expected:
            self.assertIn(part, content)

    @mock.patch(f'{mail.__name__}.smtplib.SMTP')
    def test_send_text_and_html(self, mock_SMTP):
        """Send an email with text and HTML."""
        mock_SMTP_instance = mock.MagicMock()
        mock_SMTP.return_value.__enter__.return_value = mock_SMTP_instance
        html_body = "<html><body><h1>Hi</h1><p>there!</p></body></html>"
        mail.send("erick.peirson@gmail.com", "Subject!", "Hi there.",
                  html_body=html_body)
        sent_message = str(mock_SMTP_instance.send_message.call_args[0][0])
        expected_headers = [
            'Subject: Subject!',
            'From: noreply@arxiv.org',
            'To: erick.peirson@gmail.com',
            'MIME-Version: 1.0',
            'Content-Type: multipart/alternative;'
        ]
        text_part = [
            'Content-Type: text/plain; charset="utf-8"',
            'Content-Transfer-Encoding: 7bit',
            'Hi there.'
        ]
        html_part = [
            'Content-Type: text/html; charset="utf-8"',
            'Content-Transfer-Encoding: 7bit',
            'MIME-Version: 1.0',
            '<html><body><h1>Hi</h1><p>there!</p></body></html>'
        ]
        for header in expected_headers:
            self.assertIn(header, sent_message)
        for part in text_part:
            self.assertIn(part, sent_message)
        for part in html_part:
            self.assertIn(part, sent_message)
