from __future__ import annotations

from fastapi.testclient import TestClient

from app import beta_readiness
from app.main import app


def test_production_beta_readiness_exposes_only_execution_lock_evidence(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-placeholder")
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "private-app-secret")
    monkeypatch.setenv("CRON_SECRET", "private-cron-secret")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-private")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret-private")
    monkeypatch.setenv("META_APP_ID", "meta-private")
    monkeypatch.setenv("META_APP_SECRET", "meta-secret-private")
    monkeypatch.setenv("SMTP_HOST", "smtp.private.test")

    with TestClient(app) as client:
        response = client.get("/health/beta-readiness")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "brand": "Vexmera",
        "phase": "private_beta",
        "external_execution_enabled": False,
        "autopilot_execution_enabled": False,
        "meta_execution_scope_enabled": False,
        "dev_show_tokens_enabled": False,
        "private_beta_execution_safe": True,
        "production_transport_safe": True,
    }

    rendered = response.text
    for forbidden in (
        "database",
        "stripe",
        "google_oauth",
        "meta_oauth",
        "smtp",
        "core_internal_secrets",
        "private-app-secret",
        "private-cron-secret",
        "postgresql://private-placeholder",
        "sk_test_private",
        "whsec_private",
        "google-secret-private",
        "meta-secret-private",
        "smtp.private.test",
    ):
        assert forbidden not in rendered


def test_local_beta_readiness_keeps_operator_diagnostics(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    snapshot = beta_readiness.beta_safety_snapshot()
    assert "database" in snapshot
    assert "pilot_readiness" in snapshot
    assert "privacy_controls" in snapshot
