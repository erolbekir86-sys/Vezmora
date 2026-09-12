from __future__ import annotations

import hashlib

from app import auth


def test_new_password_records_are_versioned_and_use_current_work_factor():
    salt_record, digest = auth.hash_password("correct horse battery staple")

    prefix, iterations, salt_hex = salt_record.split("$", 2)
    assert prefix == "pbkdf2_sha256"
    assert int(iterations) == auth.PBKDF2_ITERATIONS == 600_000
    assert len(bytes.fromhex(salt_hex)) == 16
    assert len(bytes.fromhex(digest)) == hashlib.sha256().digest_size
    assert auth.verify_password("correct horse battery staple", salt_record, digest) is True
    assert auth.verify_password("wrong password", salt_record, digest) is False


def test_legacy_310k_hex_salt_records_remain_valid(monkeypatch):
    salt = bytes.fromhex("00112233445566778899aabbccddeeff")
    password = "legacy-password"
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        auth.LEGACY_PBKDF2_ITERATIONS,
    ).hex()

    padding_calls: list[int] = []
    original = hashlib.pbkdf2_hmac

    def recording_pbkdf2(name, password_bytes, salt_bytes, iterations, *args, **kwargs):
        if password_bytes == b"vexmera-legacy-kdf-padding":
            padding_calls.append(iterations)
        return original(name, password_bytes, salt_bytes, iterations, *args, **kwargs)

    monkeypatch.setattr(auth.hashlib, "pbkdf2_hmac", recording_pbkdf2)

    assert auth.verify_password(password, salt.hex(), digest) is True
    assert padding_calls == [auth.PBKDF2_ITERATIONS - auth.LEGACY_PBKDF2_ITERATIONS]


def test_unknown_or_future_password_scheme_fails_closed():
    digest = "00" * hashlib.sha256().digest_size

    assert auth.verify_password("secret", "argon2id$2$00", digest) is False
    assert auth.verify_password("secret", "pbkdf2_sha256$700000$00", digest) is False
    assert auth.verify_password("secret", "pbkdf2_sha256$not-a-number$00", digest) is False


def test_current_dummy_hash_work_matches_current_iteration_policy(monkeypatch):
    calls: list[int] = []
    original = hashlib.pbkdf2_hmac

    def recording_pbkdf2(name, password_bytes, salt_bytes, iterations, *args, **kwargs):
        calls.append(iterations)
        return original(name, password_bytes, salt_bytes, iterations, *args, **kwargs)

    monkeypatch.setattr(auth.hashlib, "pbkdf2_hmac", recording_pbkdf2)
    auth.hash_password("dummy", bytes.fromhex("aabbccddeeff00112233445566778899"))

    assert calls == [auth.PBKDF2_ITERATIONS]
