"""Tests for :mod:`legacy_users.passwords`."""

from unittest import TestCase
from ..exceptions import PasswordAuthenticationFailed
from ..passwords import hash_password, check_password

from hypothesis import given, settings
from hypothesis import strategies as st
import string


class TestCheckPassword(TestCase):
    """Tests passwords."""
    @given(st.text(alphabet=string.printable))
    @settings(max_examples=500)
    def test_check_passwords_successful(self, passw):
        encrypted = hash_password(passw)
        self.assertTrue( check_password(passw, encrypted.encode('ascii')),
                         f"should work for password '{passw}'")

    @given(st.text(alphabet=string.printable), st.text(alphabet=st.characters()))
    @settings(max_examples=5000)
    def test_check_passwords_fuzz(self, passw, fuzzpw):
        if passw == fuzzpw:
            self.assertTrue(check_password(fuzzpw,
                                hash_password(passw).encode('ascii')))
        else:
            with self.assertRaises(PasswordAuthenticationFailed):
                check_password(fuzzpw,
                                    hash_password(passw).encode('ascii'))
