"""Functions to create hashes for clickthrough links.

These are used to log to the web acccess logs when the DOI and
bookmarking links are clicked.

The hash is used to prevent malicious use of the click through
controller to create links that look like they are on arXiv but get
redirected someplace undesirable.
"""

from typing import Callable
import hashlib
from flask import url_for, current_app


def create_hash(secret: str, url: str) -> str:
    """Create a hash of the secret and url."""
    s = f'{secret}{url}'
    return str(hashlib.md5(s.encode()).hexdigest()[0:8])


def is_hash_valid(secret: str, url: str, ct_hash: str) -> bool:
    """Check that ct_hash was generated by create_hash for secret and url."""
    return ct_hash == create_hash(secret, url)


def clickthrough_url(url: str) -> str:
    """Create a URL to the clickthrough service with a valid hash."""
    secret = current_app.config.get('CLICKTHROUGH_SECRET', 'foo')
    ct_url: str = url_for('clickthrough', url=url, v=create_hash(secret, url))
    return ct_url
