import hashlib

import pytest
from fastapi import HTTPException, Response

import app.auth as auth


def test_session_token_hash_rejects_oversized_and_non_ascii_input():
    assert auth._session_token_hash("a" * (auth.SESSION_TOKEN_MAX_LENGTH + 1)) is None
    assert auth._session_token_hash("sessión") is None


def test_require_user_rejects_oversized_cookie_before_store_lookup(monkeypatch):
    def unexpected_lookup(_token_hash: str):
        raise AssertionError("oversized session cookies must not reach the session store")

    monkeypatch.setattr(auth, "get_session_user", unexpected_lookup)

    with pytest.raises(HTTPException) as exc_info:
        auth.require_user("a" * (auth.SESSION_TOKEN_MAX_LENGTH + 1))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session expired or invalid"


def test_require_user_preserves_valid_session_lookup(monkeypatch):
    raw = "a" * 43
    expected_hash = hashlib.sha256(raw.encode("ascii")).hexdigest()
    expected_user = {"id": 7, "email": "pilot@example.com"}

    def lookup(token_hash: str):
        assert token_hash == expected_hash
        return expected_user

    monkeypatch.setattr(auth, "get_session_user", lookup)

    assert auth.require_user(raw) == expected_user


def test_logout_skips_store_revoke_for_invalid_cookie_but_still_deletes_cookie(monkeypatch):
    revoked: list[str] = []
    monkeypatch.setattr(auth, "revoke_session", revoked.append)
    response = Response()

    auth.end_session(response, "a" * (auth.SESSION_TOKEN_MAX_LENGTH + 1))

    assert revoked == []
    assert auth.SESSION_COOKIE in response.headers.get("set-cookie", "")
