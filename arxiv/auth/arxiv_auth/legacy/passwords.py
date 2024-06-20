"""Passwords from legacy."""

import secrets
from base64 import b64encode, b64decode
import hashlib
import logging

from .exceptions import PasswordAuthenticationFailed


def _hash_salt_and_password(salt: bytes, password: str) -> bytes:
    return hashlib.sha1(salt + b'-' + password.encode('ascii')).digest()


def hash_password(password: str) -> str:
    """Generate a secure hash of a password.

    The password must be ascii.
    """
    salt = secrets.token_bytes(4)
    hashed = _hash_salt_and_password(salt, password)
    return b64encode(salt + hashed).decode('ascii')


def check_password(password: str, encrypted: bytes):
    """Check a password against an encrypted hash."""
    try:
        password.encode('ascii')
    except UnicodeEncodeError:
        raise PasswordAuthenticationFailed('Password not ascii')

    decoded = b64decode(encrypted)
    salt = decoded[:4]
    enc_hashed = decoded[4:]
    pass_hashed = _hash_salt_and_password(salt, password)
    if pass_hashed != enc_hashed:
        raise PasswordAuthenticationFailed('Incorrect password')
    else:
        return True


def is_ascii(string):
    """Returns true if the string is only ascii chars."""
    try:
        string.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False
