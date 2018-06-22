"""Tests for :mod:`arxiv.util.schema`."""

from unittest import TestCase, mock
import json
import os
import tempfile

from arxiv import util
from arxiv import status


class TestValidateRequest(TestCase):
    """Add request body validation to a Flask route."""

    def setUp(self):
        """Initialize a :class:`.Flask` app and write a schema."""
        _, self.schema_path = tempfile.mkstemp()
        schema_body = json.dumps({
            "title": "FooResource",
            "additionalProperties": False,
            "required": ["baz", "bat"],
            "type": "object",
            "properties": {
                "baz": {
                    "type": "string"
                },
                "bat": {
                    "type": "integer"
                }
            }
        })
        with open(self.schema_path, 'w') as f:
            f.write(schema_body)

    def tearDown(self):
        """Clean up the temporary file used for the schema."""
        os.remove(self.schema_path)

    def test_decorate_route(self):
        """:func:`.schema.validate_request` generates a decorator."""
        decorator = util.schema.validate_request(self.schema_path)
        self.assertTrue(hasattr(decorator, '__call__'))

    @mock.patch('arxiv.util.schema.request')
    def test_validate_with_invalid_request_data(self, mock_request):
        """Decorated route function returns 400 bad request on invalid data."""
        mock_request.get_json = mock.MagicMock(
            return_value={'not': 'what you expected'}
        )

        decorator = util.schema.validate_request(self.schema_path)

        @decorator
        def foo_route():
            return {}, status.HTTP_200_OK, {}

        r_body, r_status, r_headers = foo_route()
        self.assertEqual(r_status, status.HTTP_400_BAD_REQUEST,
                         "Failed to catch an invalid request.")
        self.assertIn('reason', r_body)

    @mock.patch('arxiv.util.schema.request')
    def test_validate_with_valid_request_data(self, mock_request):
        """Decorated route function returns normally on valid data."""
        mock_request.get_json = mock.MagicMock(
            return_value={'baz': 'asdf', 'bat': -1}
        )

        decorator = util.schema.validate_request(self.schema_path)

        @decorator
        def foo_route():
            return {}, status.HTTP_200_OK, {}

        r_body, r_status, r_headers = foo_route()
        self.assertEqual(r_status, status.HTTP_200_OK,
                         "Interfered with a valid request")


class TestValidateSchema(TestCase):
    """Validate data against a JSON Schema specification."""

    def setUp(self):
        """Provision a temporary file for the schema."""
        _, self.schema_path = tempfile.mkstemp()

    def tearDown(self):
        """Clean up the temporary file used for the schema."""
        os.remove(self.schema_path)

    def test_load_valid_schema(self):
        """:func:`.schema.load` returns a callable validator."""
        schema_body = json.dumps({
            "title": "FooResource",
            "additionalProperties": False,
            "required": ["baz", "bat"],
            "type": "object",
            "properties": {
                "baz": {
                    "type": "string"
                },
                "bat": {
                    "type": "integer"
                }
            }
        })

        with open(self.schema_path, 'w') as f:
            f.write(schema_body)

        try:
            validator = util.schema.load(self.schema_path)
        except Exception as e:
            self.fail('Failed to load valid schema: %s' % e)
        self.assertTrue(hasattr(validator, '__call__'))

        try:
            validator({'baz': 'asdf', 'bat': -1})
        except util.schema.ValidationError as e:
            self.fail('Validation failed on valid data: %s' % e)

    def test_load_invalid_schema(self):
        """:func:`.util.schema.load` raises IOError if schema is not valid JSON."""
        with open(self.schema_path, 'w') as f:
            f.write('thisisnotajsons..."."{{chema')

        with self.assertRaises(IOError):
            util.schema.load(self.schema_path)

    def test_load_nonexistant_schema(self):
        """:func:`.util.schema.load` raises IOError if schema does not exist."""
        with self.assertRaises(IOError):
            util.schema.load('/tmp/is/unlikely/to/exist')

    def test_validation_failed(self):
        """Validator raises :class:`.util.schema.ValidationError` on bad data."""
        schema_body = json.dumps({
            "title": "FooResource",
            "additionalProperties": False,
            "required": ["baz", "bat"],
            "type": "object",
            "properties": {
                "baz": {
                    "type": "string"
                },
                "bat": {
                    "type": "integer"
                }
            }
        })
        with open(self.schema_path, 'w') as f:
            f.write(schema_body)

        validator = util.schema.load(self.schema_path)

        with self.assertRaises(util.schema.ValidationError):
            validator({'nobody': 'expects', 'thespanish': 'inquisition'})
