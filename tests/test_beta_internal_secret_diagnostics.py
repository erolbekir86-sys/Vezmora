from __future__ import annotations

from app import beta_readiness


def test_core_internal_secret_diagnostic_requires_both_values(monkeypatch):
    monkeypatch.delenv("VEZMORA_SECRET_KEY", raising=False)
    monkeypatch.delenv("CRON_SECRET", raising=False)
    assert beta_readiness.beta_safety_snapshot()["core_internal_secrets_configured"] is False

    monkeypatch.setenv("VEZMORA_SECRET_KEY", "configured-value-a")
    assert beta_readiness.beta_safety_snapshot()["core_internal_secrets_configured"] is False

    monkeypatch.setenv("CRON_SECRET", "configured-value-b")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["core_internal_secrets_configured"] is True
    assert "configured-value-a" not in str(snapshot)
    assert "configured-value-b" not in str(snapshot)
