"""Tests for :mod:`arxiv.base.messages`."""

from unittest import TestCase, mock
from flask import Markup

from arxiv.base import messages


class TestFlashInfo(TestCase):
    """Tests for :func:`messages.flash_info`."""

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        messages.flash_info('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.INFO)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        messages.flash_info('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, messages.INFO)

    @mock.patch(f'{messages.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        messages.flash_info('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.INFO)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        messages.flash_info('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.INFO)
        self.assertIsInstance(data['message'], str)


class TestFlashWarning(TestCase):
    """Tests for :func:`messages.flash_warning`."""

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        messages.flash_warning('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.WARNING)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        messages.flash_warning('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, messages.WARNING)

    @mock.patch(f'{messages.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        messages.flash_warning('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.WARNING)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        messages.flash_warning('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.WARNING)
        self.assertIsInstance(data['message'], str)


class TestFlashFailure(TestCase):
    """Tests for :func:`messages.flash_failure`."""

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        messages.flash_failure('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.FAILURE)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        messages.flash_failure('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, messages.FAILURE)

    @mock.patch(f'{messages.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        messages.flash_failure('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.FAILURE)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        messages.flash_failure('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.FAILURE)
        self.assertIsInstance(data['message'], str)


class TestFlashSuccess(TestCase):
    """Tests for :func:`messages.flash_success`."""

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message(self, mock_flash):
        """Just flash a simple message."""
        messages.flash_success('The message')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.SUCCESS)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_no_dismiss(self, mock_flash):
        """Flash a simple message that can't be dismissed."""
        messages.flash_success('The message', dismissable=False)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], str)
        self.assertFalse(data['dismissable'])
        self.assertEqual(category, messages.SUCCESS)

    @mock.patch(f'{messages.__name__}.flash')
    def test_safe_flash_message(self, mock_flash):
        """Flash a simple message that is HTML-safe."""
        messages.flash_success('The message', safe=True)
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertIsInstance(data['message'], Markup)
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.SUCCESS)

    @mock.patch(f'{messages.__name__}.flash')
    def test_flash_message_with_title(self, mock_flash):
        """Just flash a simple message with a title."""
        messages.flash_success('The message', title='Foo title')
        (data, category), kwargs = mock_flash.call_args
        self.assertEqual(data['message'], 'The message')
        self.assertEqual(data['title'], 'Foo title')
        self.assertTrue(data['dismissable'])
        self.assertEqual(category, messages.SUCCESS)
        self.assertIsInstance(data['message'], str)
