from __future__ import annotations

from fastapi.testclient import TestClient

import app.public_health as public_health
from app.auth import SESSION_COOKIE
from app.main import app


def test_vercel_health_restores_only_safe_status_for_valid_product_session(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value-that-must-not-render")
    monkeypatch.setattr(public_health, "require_user", lambda raw: {"id": 1} if raw == "valid-session" else None)
    monkeypatch.setattr(public_health, "scheduler_enabled", lambda: True)

    with TestClient(app) as client:
        client.cookies.set(SESSION_COOKIE, "valid-session")
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "vexmera",
        "version": "0.6.1",
        "model": public_health.MODEL,
        "api_key_configured": True,
        "scheduler_enabled": True,
    }
    rendered = response.text.lower()
    for forbidden in (
        "test-secret-value-that-must-not-render",
        "oauth_secret_configured",
        "stripe_configured",
        "smtp_configured",
        "storage_backend",
        "data_path",
        "worker_enabled",
    ):
        assert forbidden not in rendered


def test_vercel_health_fails_closed_to_public_payload_when_session_validation_fails(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    def fail_validation(_: str):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(public_health, "require_user", fail_validation)

    with TestClient(app) as client:
        client.cookies.set(SESSION_COOKIE, "unverifiable-session")
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "vexmera",
        "version": "0.6.1",
    }
    assert "api_key_configured" not in response.text
    assert "scheduler_enabled" not in response.text
