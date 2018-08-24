"""Tests for :mod:`arxiv.base.alerts`."""

from unittest import TestCase, mock
from flask import Markup

from arxiv.base import alerts


class TestFlashInfo(TestCase):
    """Tests for :func:`alerts.flash_info`."""

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        alerts.flash_info('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.INFO)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        alerts.flash_info('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, alerts.INFO)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        alerts.flash_info('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.INFO)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        alerts.flash_info('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.INFO)
        self.assertIsInstance(data['message'], str)


class TestFlashWarning(TestCase):
    """Tests for :func:`alerts.flash_warning`."""

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        alerts.flash_warning('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.WARNING)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        alerts.flash_warning('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, alerts.WARNING)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        alerts.flash_warning('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.WARNING)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        alerts.flash_warning('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.WARNING)
        self.assertIsInstance(data['message'], str)


class TestFlashFailure(TestCase):
    """Tests for :func:`alerts.flash_failure`."""

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        alerts.flash_failure('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.FAILURE)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        alerts.flash_failure('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, alerts.FAILURE)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        alerts.flash_failure('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.FAILURE)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        alerts.flash_failure('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.FAILURE)
        self.assertIsInstance(data['message'], str)


class TestFlashSuccess(TestCase):
    """Tests for :func:`alerts.flash_success`."""

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        alerts.flash_success('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.SUCCESS)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        alerts.flash_success('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, alerts.SUCCESS)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        alerts.flash_success('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.SUCCESS)

    @mock.patch(f'{alerts.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        alerts.flash_success('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, alerts.SUCCESS)
        self.assertIsInstance(data['message'], str)
