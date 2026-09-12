from __future__ import annotations

from app import beta_readiness


def test_legacy_turso_url_without_auth_token_is_not_remote_ready(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://private-beta.invalid")

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["database"]["backend_intent"] == "turso"
    assert snapshot["database"]["turso_url_configured"] is True
    assert snapshot["database"]["turso_auth_token_configured"] is False
    assert snapshot["database"]["remote_database_configured"] is False
    assert "remote_database_configured" in snapshot["pilot_readiness"]["configuration_blockers"]


def test_legacy_turso_requires_url_and_auth_token_without_exposing_values(monkeypatch):
    secret_url = "libsql://private-beta-secret.invalid"
    secret_token = "private-turso-auth-token"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.setenv("TURSO_DATABASE_URL", secret_url)
    monkeypatch.setenv("TURSO_AUTH_TOKEN", secret_token)

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["database"]["backend_intent"] == "turso"
    assert snapshot["database"]["turso_url_configured"] is True
    assert snapshot["database"]["turso_auth_token_configured"] is True
    assert snapshot["database"]["remote_database_configured"] is True
    rendered = str(snapshot)
    assert secret_url not in rendered
    assert secret_token not in rendered
