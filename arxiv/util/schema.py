"""Provides JSON Schema validation tools."""

import json
import os
from functools import wraps
from typing import Callable, Tuple, Any
import jsonschema
from flask import request

ValidationError = jsonschema.exceptions.ValidationError

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400


def load(schema_path: str) -> Callable:
    """
    Load a JSON Schema from ``schema_path`` and generate a validator.

    Parameters
    ----------
    schema_path : str
        Location of the target schema.

    Returns
    -------
    callable
        A validator function; when called with a ``dict``, validates the data
        against the schema.

    """
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except json.decoder.JSONDecodeError as ex:
        raise IOError('Could not load %s: %s' % (schema_path, ex)) from ex

    schema_base_path = os.path.dirname(os.path.realpath(schema_path))
    resolver = jsonschema.RefResolver(referrer=schema,
                                      base_uri="file://%s/" % schema_base_path)

    def validate(data: dict) -> None:
        """
        Validate ``data`` against the enclosed schema.

        Parameters
        ----------
        data : dict

        Raises
        ------
        :class:`.ValidationError`

        """
        jsonschema.validate(data, schema, resolver=resolver)
    return validate


def validate_request(schema_path: str) -> Callable:
    """
    Generate a route decorator that validates the request body.

    Parameters
    ----------
    schema_path : str
        Path (absolute, or relative to the execution path) to the JSON Schema
        document.

    Returns
    -------
    decorator
        Decorates a Flask route with request body validation against the
        specified JSON Schema.

    Examples
    --------
    Should be used with a Flask route, for example:

        from util import schema

        @blueprint.route('/foo/', methods=['POST'])
        @schema.validate_request('schema/resources/foo.json')
        def some_route() -> Tuple[dict, int, dict]:
            ...

    """
    validate = load(schema_path)

    def _decorator(func: Callable) -> Callable:
        @wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Tuple[dict, int, dict]:
            try:
                validate(request.get_json())
            except ValidationError as ex:
                # A summary of the exception is on the first line of the repr.
                msg = str(ex).split('\n')[0]
                return (
                    {'reason': 'Metadata validation failed: %s' % msg},
                    HTTP_400_BAD_REQUEST,
                    {}
                )
            response: Tuple[dict, int, dict] = func(*args, **kwargs)
            return response
        return _wrapper
    return _decorator
