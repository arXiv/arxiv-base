"""Context processors."""

from flask import Flask

from arxiv.base import alerts, config


def inject_get_alerts() -> dict:
    """Insert :func:`alerts.get_alerts` into the template context."""
    return dict(get_alerts=alerts.get_alerts)


def inject_get_hidden_alerts() -> dict:
    """Insert :func:`alerts.get_hidden_alerts` into the template context."""
    return dict(get_hidden_alerts=alerts.get_hidden_alerts)

def inject_a11y_url() -> dict:
    """Insert local config variable `A11Y_URL` into the template context."""
    return dict(A11Y_URL=config.A11Y_URL)

def register_context_processors(app: Flask) -> None:
    """
    Register base context processors on a Flask app.

    Parameters
    ----------
    app : :class:`Flask`

    """
    app.context_processor(inject_get_alerts)
    app.context_processor(inject_get_hidden_alerts)
    app.context_processor(inject_a11y_url)
