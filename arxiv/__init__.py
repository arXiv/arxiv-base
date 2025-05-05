"""Arxiv pacakges from arxiv-base."""

import contextvars


def is_in_flask_context():
    """Checks if currently in a Flask context without importing flask."""
    return any(
        var.name in {'app', 'request'}
        for var in contextvars.copy_context()
    )
