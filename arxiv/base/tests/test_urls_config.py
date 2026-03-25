"""Tests for URLS config via env vars in :class:`.Base`."""
from _pytest import monkeypatch
import pytest
from unittest import TestCase

from flask import Flask, url_for

from arxiv.base.config import CANONICAL_SERVER

from .. import Base

AUTH_SERVER_VALUE="auth.example.com"
HELP_SERVER_VALUE="help.example.com"
CANONICAL_SERVER_VALUE="canonical.example.com"
SUBMIT_SERVER_VALUE="submit.example.com"
SEARCH_SERVER_VALUE="search.example.com"

@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("AUTH_SERVER", AUTH_SERVER_VALUE)
    monkeypatch.setenv("HELP_SERVER", HELP_SERVER_VALUE)
    monkeypatch.setenv("CANONICAL_SERVER", CANONICAL_SERVER_VALUE)
    monkeypatch.setenv("SUBMIT_SERVER", SUBMIT_SERVER_VALUE)
    monkeypatch.setenv("SEARCH_SERVER", SEARCH_SERVER_VALUE)
    app = Flask(__name__)
    Base(app)
    return app


@pytest.mark.parametrize("urlfor, path, server", [
    ('about','/about',HELP_SERVER_VALUE),
    ('login', '/login', AUTH_SERVER_VALUE),
    ('create','/user/create', SUBMIT_SERVER_VALUE),
    ('search_box', 'search', SEARCH_SERVER_VALUE),
])

def test_server_configed_urls(app, urlfor, path, server):
    with app.test_request_context('/home', method='GET'):
        assert "https://" + server + path == url_for(urlfor)
