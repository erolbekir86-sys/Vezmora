from __future__ import annotations

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.http_error_safety import install_http_error_safety, sanitize_http_detail


def test_http_error_safety_redacts_meta_and_generic_token_patterns(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "meta-secret-123")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret-456")

    detail = {
        "message": "Meta failed with access_token=meta-access-abc and meta-secret-123",
        "nested": [
            "Bearer bearer-token-xyz",
            "client_secret=inline-client-secret",
            "google-secret-456",
        ],
        "code": 190,
    }

    sanitized = sanitize_http_detail(detail)
    rendered = str(sanitized)

    assert "meta-access-abc" not in rendered
    assert "meta-secret-123" not in rendered
    assert "bearer-token-xyz" not in rendered
    assert "inline-client-secret" not in rendered
    assert "google-secret-456" not in rendered
    assert sanitized["code"] == 190
    assert rendered.count("[REDACTED]") >= 5


def test_http_error_safety_redacts_all_runtime_secret_surfaces(monkeypatch):
    secrets = {
        "VEZMORA_SECRET_KEY": "session-fernet-secret",
        "STRIPE_WEBHOOK_SECRET": "whsec_private_123",
        "SMTP_PASSWORD": "smtp-pass-456",
        "TURSO_AUTH_TOKEN": "turso-token-789",
        "DATABASE_URL": "postgresql://user:dbpass@primary.example/vexmera",
        "POSTGRES_URL": "postgresql://user:otherpass@pool.example/vexmera",
        "TURSO_DATABASE_URL": "libsql://private-db.turso.io",
    }
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)

    detail = {
        "message": (
            "runtime error session-fernet-secret whsec_private_123 smtp-pass-456 "
            "turso-token-789 postgresql://user:dbpass@primary.example/vexmera"
        ),
        "nested": [
            "postgresql://user:otherpass@pool.example/vexmera",
            "libsql://private-db.turso.io",
            "password=inline-password",
            "webhook_secret=inline-whsec",
            "auth_token=inline-auth-token",
        ],
        "safe_context": "customer_id=123456789 and plan=growth",
    }

    sanitized = sanitize_http_detail(detail)
    rendered = str(sanitized)

    for secret in (*secrets.values(), "inline-password", "inline-whsec", "inline-auth-token"):
        assert secret not in rendered
    assert "customer_id=123456789" in rendered
    assert "plan=growth" in rendered
    assert rendered.count("[REDACTED]") >= 10


def test_http_error_safety_redacts_inline_auth_capabilities():
    detail = {
        "message": "reset_token=reset-abc invite_token:invite-def",
        "nested": [
            "session_token=session-ghi",
            "oauth_state=oauth-jkl",
        ],
        "safe_context": "workspace_id=42",
    }

    sanitized = sanitize_http_detail(detail)
    rendered = str(sanitized)

    for capability in ("reset-abc", "invite-def", "session-ghi", "oauth-jkl"):
        assert capability not in rendered
    assert "workspace_id=42" in rendered
    assert rendered.count("[REDACTED]") >= 4


def test_http_error_safety_preserves_actionable_non_secret_meta_context():
    detail = {
        "message": "Meta ad account lookup failed: Unsupported get request",
        "meta_code": 100,
        "meta_subcode": 33,
    }

    assert sanitize_http_detail(detail) == detail


def test_unhandled_httpx_transport_error_becomes_secret_safe_502():
    app = FastAPI()
    secret = "meta-access-token-must-not-render"

    @app.get("/provider")
    def provider():
        request = httpx.Request(
            "GET",
            f"https://graph.facebook.com/v24.0/me/adaccounts?access_token={secret}",
        )
        raise httpx.ConnectError("connection failed", request=request)

    install_http_error_safety(app)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/provider")

    assert response.status_code == 502
    assert response.json() == {"detail": "Upstream provider connection failed. Try again later."}
    assert response.headers["cache-control"] == "no-store"
    assert secret not in response.text
    assert "graph.facebook.com" not in response.text
