from __future__ import annotations

from fastapi.testclient import TestClient

from app import beta_readiness
from app.main import app


def _clear(monkeypatch):
    for name in (
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
        "VEZMORA_DEV_SHOW_TOKENS",
        "VEZMORA_APP_URL",
        "VEZMORA_COOKIE_SECURE",
        "VERCEL",
        "VERCEL_ENV",
        "STRIPE_PRICE_STARTER",
        "STRIPE_PRICE_GROWTH",
        "STRIPE_PRICE_SCALE",
        "STRIPE_WEBHOOK_SECRET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_ID",
        "META_APP_SECRET",
        "META_REDIRECT_URI",
        "SMTP_HOST",
        "SMTP_FROM",
    ):
        monkeypatch.delenv(name, raising=False)


def test_beta_readiness_is_safe_by_default_and_reports_privacy_controls(monkeypatch):
    _clear(monkeypatch)
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["private_beta_execution_safe"] is True
    assert snapshot["production_transport_safe"] is True
    assert snapshot["external_execution_enabled"] is False
    assert snapshot["autopilot_execution_enabled"] is False
    assert snapshot["meta_execution_scope_enabled"] is False
    assert snapshot["dev_show_tokens_enabled"] is False
    assert snapshot["privacy_controls"] == {
        "connector_disconnect": True,
        "scoped_synced_history_deletion": True,
        "full_account_deletion": False,
    }


def test_beta_readiness_detects_unsafe_execution_flags(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_EXECUTION_ENABLED", "true")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["external_execution_enabled"] is True
    assert snapshot["private_beta_execution_safe"] is False


def test_beta_readiness_treats_dev_token_exposure_as_unsafe(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_DEV_SHOW_TOKENS", "true")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["dev_show_tokens_enabled"] is True
    assert snapshot["private_beta_execution_safe"] is False


def test_beta_readiness_detects_insecure_production_transport(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "http://example.test")
    monkeypatch.setenv("VEZMORA_COOKIE_SECURE", "false")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["production_transport_safe"] is False
    assert snapshot["transport"] == {
        "production_like": True,
        "app_url_configured": True,
        "app_url_https": False,
        "secure_cookie_explicitly_disabled": True,
        "safe": False,
    }


def test_beta_readiness_accepts_secure_production_transport(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["production_transport_safe"] is True
    assert snapshot["transport"]["app_url_https"] is True
    assert snapshot["transport"]["secure_cookie_explicitly_disabled"] is False


def test_beta_readiness_endpoint_never_returns_secret_values(monkeypatch):
    _clear(monkeypatch)
    values = {
        "VEZMORA_APP_URL": "https://example.test",
        "STRIPE_PRICE_STARTER": "price_private_starter",
        "STRIPE_PRICE_GROWTH": "price_private_growth",
        "STRIPE_PRICE_SCALE": "price_private_scale",
        "STRIPE_WEBHOOK_SECRET": "whsec_private",
        "GOOGLE_CLIENT_ID": "google-client-private",
        "GOOGLE_CLIENT_SECRET": "google-secret-private",
        "GOOGLE_REDIRECT_URI": "https://example.test/google",
        "GOOGLE_ADS_DEVELOPER_TOKEN": "google-ads-private",
        "META_APP_ID": "meta-app-private",
        "META_APP_SECRET": "meta-secret-private",
        "META_REDIRECT_URI": "https://example.test/meta",
        "SMTP_HOST": "smtp.example.test",
        "SMTP_FROM": "sender@example.test",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    with TestClient(app) as client:
        response = client.get("/health/beta-readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stripe_catalog_env_configured"] is True
    assert payload["stripe_webhook_env_configured"] is True
    assert payload["google_oauth_configured"] is True
    assert payload["google_ads_developer_token_configured"] is True
    assert payload["meta_oauth_configured"] is True
    assert payload["smtp_minimum_configured"] is True
    assert payload["production_transport_safe"] is True

    rendered = response.text
    for secret in values.values():
        assert secret not in rendered
