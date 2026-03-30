"""Tests for URLS config via env vars in :class:`.Base`."""
import importlib
from _pytest import monkeypatch
import pytest

from flask import Flask, url_for



AUTH_SERVER_VALUE="auth.example.com"
HELP_SERVER_VALUE="help.example.com"
CANONICAL_SERVER_VALUE="canonical.example.com"
SUBMIT_SERVER_VALUE="submit.example.com"
SEARCH_SERVER_VALUE="search.example.com"

@pytest.fixture
def app_with_envvars(monkeypatch):
    monkeypatch.setenv("AUTH_SERVER", AUTH_SERVER_VALUE)
    monkeypatch.setenv("HELP_SERVER", HELP_SERVER_VALUE)
    monkeypatch.setenv("CANONICAL_SERVER", CANONICAL_SERVER_VALUE)
    monkeypatch.setenv("SUBMIT_SERVER", SUBMIT_SERVER_VALUE)
    monkeypatch.setenv("SEARCH_SERVER", SEARCH_SERVER_VALUE)

    import os
    assert os.environ.get("AUTH_SERVER") == AUTH_SERVER_VALUE

    import arxiv.config
    importlib.reload(arxiv.config)
    from arxiv.config import settings

    from .. import Base
    app_with_envvars = Flask(__name__)
    app_with_envvars.config.from_object(settings)
    Base(app_with_envvars)
    return app_with_envvars

def test_monkeypatch_set_envvars(app_with_envvars):
    with app_with_envvars.test_request_context('/home', method='GET'):
        import os
        assert os.environ.get("AUTH_SERVER") == AUTH_SERVER_VALUE

def test_settings_gets_envvar(app_with_envvars):
    with app_with_envvars.test_request_context('/home', method='GET'):
        import arxiv.config
        importlib.reload(arxiv.config)
        from arxiv.config import settings
        assert settings.AUTH_SERVER == AUTH_SERVER_VALUE
        assert settings.HELP_SERVER == HELP_SERVER_VALUE
        assert settings.CANONICAL_SERVER == CANONICAL_SERVER_VALUE
        assert settings.SUBMIT_SERVER == SUBMIT_SERVER_VALUE
        assert settings.SEARCH_SERVER == SEARCH_SERVER_VALUE

@pytest.mark.parametrize("urlfor, path, server", [
    ('about','/about',HELP_SERVER_VALUE),
    ('login', '/login', AUTH_SERVER_VALUE),
    ('create','/user/create', SUBMIT_SERVER_VALUE),
    ('search_box', '/search', SEARCH_SERVER_VALUE),
])
def test_server_configed_urls(app_with_envvars, urlfor, path, server):
    with app_with_envvars.test_request_context('/home', method='GET'):
        assert "https://" + server + path == url_for(urlfor)


def test_w_base_server(monkeypatch):
    BASE = "base.arxiv.org"
    monkeypatch.setenv("BASE_SERVER", BASE)
    import arxiv.config
    importlib.reload(arxiv.config)
    from arxiv.config import settings
    app = Flask(__name__)
    app.config.from_object(settings)
    from .. import Base
    Base(app)
    with app.test_request_context('/home', method='GET'):
        import os
        assert os.environ.get("BASE_SERVER") == BASE
        from arxiv.config import settings
        assert settings.BASE_SERVER == BASE
