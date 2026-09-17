from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app import store


def _invite(email: str, token: str, *, hours: int = 24) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
    store.create_beta_invite(email, token_hash, expires)


def _payload(email: str, token: str | None = None) -> dict[str, object]:
    return {
        "email": email,
        "password": "verysecure123",
        "workspace_name": "Pilot AB",
        "beta_invite": token,
    }


def test_production_registration_requires_personal_beta_invite(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "invite-only.db")
    monkeypatch.setenv("VERCEL_ENV", "production")
    store.init_db()

    with TestClient(app) as client:
        response = client.post("/api/auth/register", json=_payload("pilot@example.com"))

    assert response.status_code == 403
    assert response.json()["detail"] == "Private beta registration requires an invitation"


def test_beta_invite_is_email_bound_one_time_and_expires(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "invite-claim.db")
    monkeypatch.setenv("VERCEL_ENV", "production")
    store.init_db()

    token = "beta_invite_personal_token_123456789"
    _invite("pilot@example.com", token)

    with TestClient(app) as client:
        mismatch = client.post("/api/auth/register", json=_payload("other@example.com", token))
        assert mismatch.status_code == 403

        accepted = client.post("/api/auth/register", json=_payload("pilot@example.com", token))
        assert accepted.status_code == 200
        assert accepted.json()["user"]["email"] == "pilot@example.com"

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert store.consume_beta_invite(token_hash, "pilot@example.com") is False

    expired_token = "beta_invite_expired_token_123456789"
    _invite("expired@example.com", expired_token, hours=-1)
    with TestClient(app) as client:
        expired = client.post("/api/auth/register", json=_payload("expired@example.com", expired_token))
    assert expired.status_code == 403
    assert expired.json()["detail"] == "Private beta invitation is invalid or expired"


def test_existing_users_can_still_login_when_registration_is_invite_only(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "existing-login.db")
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    store.init_db()

    with TestClient(app) as client:
        created = client.post("/api/auth/register", json=_payload("existing@example.com"))
        assert created.status_code == 200
        client.post("/api/auth/logout")

        monkeypatch.setenv("VERCEL_ENV", "production")
        login = client.post(
            "/api/auth/login",
            json={"email": "existing@example.com", "password": "verysecure123"},
        )

    assert login.status_code == 200


def test_product_shell_marks_production_as_invite_only(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    with TestClient(app) as client:
        page = client.get("/app")

    assert page.status_code == 200
    assert "window.__VEXMERA_INVITE_ONLY__=true" in page.text
    assert 'id="betaInviteNotice"' in page.text
    assert 'id="registerSubmit"' in page.text


def test_root_preserves_beta_invite_query_when_redirecting_to_app():
    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/?beta_invite=opaque-beta-token")

    assert response.status_code == 302
    assert response.headers["location"] == "/app?beta_invite=opaque-beta-token"
