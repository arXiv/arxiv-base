"""
These tests check for possible problems with apps that use this package.

Usage
-----
You can import all of the tests in this module, and run them with the built in
test runner. E.g.

.. code-block:: python

   # my_app_tests.py
   import unittest

   from my_app.factory import create_web_app
   from arxiv.base.app_tests import *

   app = create_web_app()

   if __name__ == '__main__':
       with app.app_context():
           unittest.main()


And run with:

.. code-block:: bash

   pipenv run python my_app_tests.py


"""

from flask import Flask, current_app
from unittest import TestCase


class TestConfig(TestCase):
    """Look for common problems with the app config."""

    def test_server_name(self):
        """SERVER_NAME should be None (or unset)."""
        self.assertIsNone(current_app.config.get('SERVER_NAME'),
                          "SERVER_NAME should be None (or unset)")


class TestStaticFiles(TestCase):
    """Make sure that static files are configured safely on an app."""

    def test_static_url_paths(self) -> None:
        """Check for possible issues with the static URL path."""
        self.assertTrue(current_app.static_url_path.startswith('/static'),
                        "The static url path for the app should start with"
                        " /static")
        self.assertIn(
            f'/{current_app.name}', current_app.static_url_path,
            f"The static_url_path should include the name of the app"
        )
        self.assertIn(
            f'/{current_app.config.get("APP_VERSION")}',
            current_app.static_url_path,
            f"The static_url_path should include the version of the app"
            " (config.APP_VERSION)"
        )

        for key, blueprint in current_app.blueprints.items():
            self.assertIsNotNone(
                blueprint.static_url_path,
                f"The static_url_path should be set on blueprint `{key}`"
            )
            self.assertTrue(current_app.static_url_path.startswith('/static'),
                            "The static url path for the app should start with"
                            " /static")
            self.assertIn(
                f'/{current_app.name}', blueprint.static_url_path,
                f"The static_url_path should include the name of the app"
            )
            self.assertIn(
                f'/{current_app.config.get("APP_VERSION")}',
                blueprint.static_url_path,
                f"The static_url_path should include the version of the app"
                " (config.APP_VERSION)"
            )
            self.assertIn(
                key, blueprint.static_url_path,
                f"The static_url_path for blueprint `{key}` should include"
                " the name of the blueprint"
            )
