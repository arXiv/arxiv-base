"""Smoke test for the spinout chrome (header/footer/announcement).

Nothing else renders ``base/header.html`` / ``base/footer.html`` /
``base/announcement_banner.html``, so a non-portable ``url_for`` endpoint in the
chrome would otherwise only surface in a consuming app (auth/search) as a 500.
Rendering ``base/base.html`` here forces every chrome ``url_for`` to resolve
through base's URL-registry fallback, catching a bad endpoint at base's own CI.
"""
from unittest import TestCase

from flask import render_template

from arxiv.base.factory import create_web_app


class TestSpinoutChromeRenders(TestCase):
    """The spinout chrome renders without a BuildError."""

    def test_base_chrome_renders(self):
        """``base/base.html`` renders; every chrome ``url_for`` resolves."""
        app = create_web_app()
        app.config["SPINOUT_BANNER_ENABLED"] = True
        with app.test_request_context("/"):
            html = render_template("base/base.html", pagetitle="Test")
        # header + footer + (enabled) announcement banner are all present.
        self.assertIn("ds-site-header", html)
        self.assertIn("ds-site-footer", html)
        self.assertIn("ds-announcement", html)
