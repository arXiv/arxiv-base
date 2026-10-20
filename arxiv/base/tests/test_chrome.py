"""Smoke test for the shared chrome (header/footer/announcement, from arxiv_brand).

Nothing else renders ``base/base.html``, so a chrome that fails to render would otherwise only
surface in a consuming app (auth/search) as a 500.
"""
from types import SimpleNamespace
from unittest import TestCase

from flask import Flask, render_template, request

from arxiv.base import Base, config as base_config
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


class TestSharedChrome(TestCase):
    """The shared chrome keeps base's sign-in state and follows the app's hosts."""

    def render(self, app, user=""):
        with app.test_request_context("/"):
            if user:
                request.session = SimpleNamespace(user=SimpleNamespace(name=user))
            return render_template("base/base.html", pagetitle="Test")

    def test_signed_out_and_in(self):
        app = create_web_app()
        self.assertIn('href="https://arxiv.org/login" class="ds-site-header-login">Log in<', self.render(app))
        self.assertIn('href="https://arxiv.org/user" class="ds-site-header-login">Account<',
                      self.render(app, user="Ada"))   # Log out is on the account page

    def test_links_follow_the_apps_hosts(self):
        app = Flask("dev_host")
        app.config.from_object(base_config)
        app.config.update(BASE_SERVER="browse.dev.arxiv.org", AUTH_SERVER="auth.dev.arxiv.org",
                          HELP_SERVER="info.dev.arxiv.org",
                          BRAND_STATIC_BASE="https://static.dev.arxiv.org/static/design-system/latest/")
        Base(app)
        html = self.render(app)
        for part in ('href="https://browse.dev.arxiv.org/search"', 'href="https://auth.dev.arxiv.org/login"',
                     'href="https://info.dev.arxiv.org/help"',
                     'src="https://static.dev.arxiv.org/static/design-system/latest/chrome/banner.js"'):
            self.assertIn(part, html)
