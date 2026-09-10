from __future__ import annotations

from fastapi.testclient import TestClient

import main as production_entrypoint


def test_vercel_runtime_diagnostics_expose_only_minimal_deployment_identity(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "abc123")
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret.invalid/db")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_secret")
    monkeypatch.setenv("SMTP_PASSWORD", "secret-smtp")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret-google")
    monkeypatch.setenv("META_APP_SECRET", "secret-meta")

    with TestClient(production_entrypoint.app) as client:
        response = client.get("/health/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "vexmera",
        "version": "0.6.1",
        "platform": "vercel",
        "environment": "production",
        "deployment_revision": "abc123",
    }


def test_local_runtime_diagnostics_remain_available_for_operator_qa(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("VERCEL_GIT_COMMIT_SHA", raising=False)

    with TestClient(production_entrypoint.app) as client:
        payload = client.get("/health/runtime").json()

    assert payload["ok"] is True
    assert "database_connection_ok" in payload
    assert "internal_secrets_configured" in payload
