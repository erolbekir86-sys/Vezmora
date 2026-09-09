from __future__ import annotations

from fastapi import Response

from app import auth


def _set_cookie_header(monkeypatch, **env: str) -> str:
    for name in ("VERCEL", "VEZMORA_COOKIE_SECURE", "VEZMORA_APP_URL"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    monkeypatch.setattr(auth, "create_session", lambda user_id, token_hash, expires_at: None)
    response = Response()
    auth.start_session(response, 123)
    return response.headers["set-cookie"]


def test_vercel_forces_secure_session_cookie_even_if_override_is_false(monkeypatch):
    header = _set_cookie_header(
        monkeypatch,
        VERCEL="1",
        VEZMORA_COOKIE_SECURE="false",
    )

    assert "Secure" in header
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert "Path=/" in header


def test_https_app_url_defaults_to_secure_session_cookie(monkeypatch):
    header = _set_cookie_header(
        monkeypatch,
        VEZMORA_APP_URL="https://beta.vexmera.example",
    )

    assert "Secure" in header


def test_local_http_can_explicitly_disable_secure_cookie_for_development(monkeypatch):
    header = _set_cookie_header(
        monkeypatch,
        VEZMORA_COOKIE_SECURE="false",
        VEZMORA_APP_URL="http://127.0.0.1:8000",
    )

    assert "Secure" not in header
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
