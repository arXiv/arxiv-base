"""Context processors."""

from flask import Flask, current_app, request

import arxiv_brand

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

def inject_brand_chrome() -> dict:
    """The shared chrome's per-request values: the signed-in state, the member
    acknowledgement (which the chrome's header.js fills in the browser from
    /institutional_banner) and whether to show the shared announcements
    (SPINOUT_BANNER_ENABLED, from the app's config, else base's environment)."""
    user = getattr(getattr(request, "session", None), "user", None)
    return arxiv_brand.context(
        signed_in=bool(user and getattr(user, "name", None)),
        member_institution='<span class="ack-member-inline" hidden>, <strong></strong></span>',
        hide_announcement=not current_app.config.get("SPINOUT_BANNER_ENABLED",
                                                     config.SPINOUT_BANNER_ENABLED),
    )


def register_context_processors(app: Flask) -> None:
    """Register base context processors on a Flask app.

    Parameters
    ----------
    app : :class:`Flask`
    """
    app.context_processor(inject_get_alerts)
    app.context_processor(inject_get_hidden_alerts)
    app.context_processor(inject_a11y_url)
    app.context_processor(inject_brand_chrome)
