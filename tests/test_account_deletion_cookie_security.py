from __future__ import annotations

from fastapi.testclient import TestClient

from app import account_privacy_controls, store  # noqa: F401
from app.main import app


PASSWORD = "verysecure123"


def test_account_deletion_expires_secure_session_cookie_with_matching_attributes(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-delete-cookie.db")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VEZMORA_COOKIE_SECURE", "false")
    store.init_db()

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={
                "email": "delete-cookie@example.com",
                "password": PASSWORD,
                "workspace_name": "Deletion Cookie Test",
            },
        )
        assert registered.status_code == 200

        response = client.request(
            "DELETE",
            "/api/privacy/account",
            json={"password": PASSWORD, "confirmation": "DELETE MY ACCOUNT"},
        )

    assert response.status_code == 200
    header = response.headers["set-cookie"]
    assert 'vezmora_session=""' in header
    assert "Max-Age=0" in header
    assert "Secure" in header
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert "Path=/" in header
