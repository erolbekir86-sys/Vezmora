from __future__ import annotations

from fastapi.testclient import TestClient

from app import beta_readiness
from app.main import app


def _base_production(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.test")


def test_production_snapshot_marks_disabled_starttls_transport_unsafe(monkeypatch):
    _base_production(monkeypatch)
    monkeypatch.setenv("SMTP_STARTTLS", "false")

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["smtp_minimum_configured"] is True
    assert snapshot["smtp_transport_ready"] is False
    assert snapshot["production_transport_safe"] is False
    assert snapshot["transport"]["smtp_starttls_required_but_disabled"] is True
    assert snapshot["pilot_readiness"]["checks"]["transactional_email_configured"] is False
    assert "production_transport_safe" in snapshot["pilot_readiness"]["configuration_blockers"]
    assert "transactional_email_configured" in snapshot["pilot_readiness"]["configuration_blockers"]


def test_production_snapshot_accepts_default_or_explicit_starttls(monkeypatch):
    _base_production(monkeypatch)
    monkeypatch.delenv("SMTP_STARTTLS", raising=False)
    default_snapshot = beta_readiness.beta_safety_snapshot()
    assert default_snapshot["smtp_transport_ready"] is True
    assert default_snapshot["production_transport_safe"] is True

    monkeypatch.setenv("SMTP_STARTTLS", "true")
    explicit_snapshot = beta_readiness.beta_safety_snapshot()
    assert explicit_snapshot["smtp_transport_ready"] is True
    assert explicit_snapshot["production_transport_safe"] is True


def test_local_operator_snapshot_keeps_plaintext_smtp_as_nonproduction_diagnostic(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.local.test")
    monkeypatch.setenv("SMTP_FROM", "local@example.test")
    monkeypatch.setenv("SMTP_STARTTLS", "false")

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["transport"]["production_like"] is False
    assert snapshot["transport"]["smtp_starttls_required_but_disabled"] is False
    assert snapshot["production_transport_safe"] is True
    assert snapshot["smtp_transport_ready"] is True


def test_public_production_readiness_exposes_only_aggregate_transport_result(monkeypatch):
    _base_production(monkeypatch)
    monkeypatch.setenv("SMTP_STARTTLS", "false")

    with TestClient(app) as client:
        response = client.get("/health/beta-readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_transport_safe"] is False
    assert "smtp_transport_ready" not in payload
    assert "smtp_minimum_configured" not in payload
    assert "transport" not in payload
    assert "SMTP_STARTTLS" not in response.text
