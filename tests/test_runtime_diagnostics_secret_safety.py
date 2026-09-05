from __future__ import annotations

import main as production_main


def test_runtime_diagnostics_exposes_only_configuration_booleans(monkeypatch):
    """The public runtime diagnostic must never echo configured secret values."""
    secrets = {
        "OPENAI_API_KEY": "openai-secret-value-123",
        "VEZMORA_SECRET_KEY": "app-secret-value-456",
        "CRON_SECRET": "cron-secret-value-789",
        "STRIPE_SECRET_KEY": "stripe-secret-value-abc",
        "STRIPE_WEBHOOK_SECRET": "stripe-webhook-secret-def",
        "SMTP_PASSWORD": "smtp-secret-value-ghi",
        "GOOGLE_CLIENT_SECRET": "google-secret-value-jkl",
        "META_APP_SECRET": "meta-secret-value-mno",
    }
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)

    monkeypatch.setattr(production_main, "_database_connection_ok", lambda: True)
    monkeypatch.setattr(production_main, "_openai_connection_ok", lambda: True)

    payload = production_main.runtime_diagnostics()
    rendered = repr(payload)

    for value in secrets.values():
        assert value not in rendered

    assert payload["openai_api_key_configured"] is True
    assert payload["app_secret_configured"] is True
    assert payload["cron_secret_configured"] is True
    assert payload["stripe_configured"] is False
    assert payload["smtp_password_configured"] is True
    assert payload["google_oauth_configured"] is False
    assert payload["meta_oauth_configured"] is False


def test_runtime_diagnostics_does_not_publish_secret_named_fields():
    payload = production_main.runtime_diagnostics()
    keys = {key.lower() for key in payload}

    forbidden_fragments = (
        "secret_value",
        "api_key_value",
        "password_value",
        "access_token",
        "refresh_token",
        "developer_token",
    )
    assert not any(fragment in key for key in keys for fragment in forbidden_fragments)
