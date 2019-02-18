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
        expected = (
            'Subject: Subject!\n'
            'From: noreply@arxiv.org\n'
            'To: erick.peirson@gmail.com\n'
            'Content-Type: text/plain; charset="utf-8"\n'
            'Content-Transfer-Encoding: 7bit\n'
            'MIME-Version: 1.0\n\n'
            'Hi there.\n'
        )
        self.assertEqual(str(mock_SMTP_instance.send_message.call_args[0][0]),
                         expected)

    @mock.patch(f'{mail.__name__}.smtplib.SMTP')
    def test_send_text_with_cc_and_bcc(self, mock_SMTP):
        """Send a text-only e-mail with CC and BCC recipients."""
        mock_SMTP_instance = mock.MagicMock()
        mock_SMTP.return_value.__enter__.return_value = mock_SMTP_instance
        mail.send("erick.peirson@gmail.com", "Subject!", "Hi there.",
                  cc_recipients=['foo@somewhere.edu', 'baz@somewhere.edu'],
                  bcc_recipients=['bar@elsewhere.edu'])
        expected = (
            'Subject: Subject!\n'
            'From: noreply@arxiv.org\n'
            'To: erick.peirson@gmail.com\n'
            'CC: foo@somewhere.edu, baz@somewhere.edu\n'
            'BCC: bar@elsewhere.edu\n'
            'Content-Type: text/plain; charset="utf-8"\n'
            'Content-Transfer-Encoding: 7bit\n'
            'MIME-Version: 1.0\n\n'
            'Hi there.\n'
        )
        self.assertEqual(str(mock_SMTP_instance.send_message.call_args[0][0]),
                         expected)

    @mock.patch(f'{mail.__name__}.smtplib.SMTP')
    def test_send_text_and_html(self, mock_SMTP):
        """Send an email with text and HTML."""
        mock_SMTP_instance = mock.MagicMock()
        mock_SMTP.return_value.__enter__.return_value = mock_SMTP_instance
        html_body = "<html><body><h1>Hi</h1><p>there!</p></body></html>"
        mail.send("erick.peirson@gmail.com", "Subject!", "Hi there.",
                  html_body=html_body)
        sent_message = str(mock_SMTP_instance.send_message.call_args[0][0])
        expected_headers = (
            'Subject: Subject!\n'
            'From: noreply@arxiv.org\n'
            'To: erick.peirson@gmail.com\n'
            'MIME-Version: 1.0\n'
            'Content-Type: multipart/alternative;\n'
        )
        text_part = (
            'Content-Type: text/plain; charset="utf-8"\n'
            'Content-Transfer-Encoding: 7bit\n\n'
            'Hi there.\n'
        )
        html_part = (
            'Content-Type: text/html; charset="utf-8"\n'
            'Content-Transfer-Encoding: 7bit\n'
            'MIME-Version: 1.0\n\n'
            '<html><body><h1>Hi</h1><p>there!</p></body></html>\n'
        )
        self.assertIn(expected_headers, sent_message)
        self.assertIn(text_part, sent_message)
        self.assertIn(html_part, sent_message)
