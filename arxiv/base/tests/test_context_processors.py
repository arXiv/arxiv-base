"""Tests for :mod:`arxiv.base.context_processors`."""

from unittest import TestCase
from flask import Flask

from arxiv.base.context_processors import config_url_builder


class TestConfigURLBuilderContextProcessor(TestCase):
    """config_url_builder() injects a URL factory into the response context."""

    def test_config_url_builder_returns_a_function(self):
        """config_url_builder() should return a dict with config_url()."""
        extra_context = config_url_builder()
        self.assertIsInstance(extra_context, dict, "Should return a dict")
        self.assertIn('config_url', extra_context,
                      "Should contain `config_url` key")
        self.assertTrue(hasattr(extra_context['config_url'], '__call__'),
                        "Value for ``config_url`` should be callable.")
