from __future__ import annotations

from app.auth import hash_password, verify_password


def test_verify_password_accepts_valid_stored_record():
    salt, digest = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", salt, digest) is True
    assert verify_password("wrong password", salt, digest) is False


def test_verify_password_fails_closed_on_malformed_hex():
    assert verify_password("secret", "not-hex", "00" * 32) is False
    assert verify_password("secret", "00" * 16, "not-hex") is False


def test_verify_password_fails_closed_on_empty_or_wrong_length_record():
    assert verify_password("secret", "", "00" * 32) is False
    assert verify_password("secret", "00" * 16, "00" * 31) is False
    assert verify_password("secret", "00" * 16, "00" * 33) is False
