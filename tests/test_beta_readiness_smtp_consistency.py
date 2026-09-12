from __future__ import annotations

from app import beta_readiness


def _configure_production_smtp(monkeypatch, *, starttls: str | None) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.delenv("VEZMORA_COOKIE_SECURE", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "sender@example.test")
    if starttls is None:
        monkeypatch.delenv("SMTP_STARTTLS", raising=False)
    else:
        monkeypatch.setenv("SMTP_STARTTLS", starttls)


def test_beta_readiness_rejects_configured_plaintext_smtp_in_production(monkeypatch):
    _configure_production_smtp(monkeypatch, starttls="false")

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["smtp_minimum_configured"] is True
    assert snapshot["smtp_transport_ready"] is False
    assert snapshot["production_transport_safe"] is False
    checks = snapshot["pilot_readiness"]["checks"]
    assert checks["transactional_email_configured"] is False
    assert checks["production_transport_safe"] is False
    blockers = snapshot["pilot_readiness"]["configuration_blockers"]
    assert "transactional_email_configured" in blockers
    assert "production_transport_safe" in blockers


def test_beta_readiness_matches_runtime_default_starttls(monkeypatch):
    _configure_production_smtp(monkeypatch, starttls=None)

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["smtp_minimum_configured"] is True
    assert snapshot["smtp_transport_ready"] is True
    assert snapshot["production_transport_safe"] is True
