from __future__ import annotations

from fastapi.testclient import TestClient

from app import beta_readiness
from app.main import app
from app.pricing import CURRENT_PRICING_VERSION


def _clear(monkeypatch):
    for name in (
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
        "VEZMORA_DEV_SHOW_TOKENS",
        "VEZMORA_SECRET_KEY",
        "CRON_SECRET",
        "VEZMORA_APP_URL",
        "VEZMORA_COOKIE_SECURE",
        "VERCEL",
        "VERCEL_ENV",
        "DATABASE_URL",
        "POSTGRES_URL",
        "TURSO_DATABASE_URL",
        "TURSO_AUTH_TOKEN",
        "STRIPE_SECRET_KEY",
        "STRIPE_PRICE_START",
        "STRIPE_PRICE_GROWTH",
        "STRIPE_PRICE_PRO",
        "VEZMORA_STRIPE_PRICING_VERSION",
        "STRIPE_WEBHOOK_SECRET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "META_APP_ID",
        "META_APP_SECRET",
        "META_REDIRECT_URI",
        "SMTP_HOST",
        "SMTP_FROM",
    ):
        monkeypatch.delenv(name, raising=False)


def _set_current_stripe_sandbox(monkeypatch, *, key: str = "sk_test_private") -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", key)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", CURRENT_PRICING_VERSION)


def test_beta_readiness_is_safe_by_default_and_reports_privacy_controls(monkeypatch):
    _clear(monkeypatch)
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["private_beta_execution_safe"] is True
    assert snapshot["production_transport_safe"] is True
    assert snapshot["external_execution_enabled"] is False
    assert snapshot["autopilot_execution_enabled"] is False
    assert snapshot["meta_execution_scope_enabled"] is False
    assert snapshot["dev_show_tokens_enabled"] is False
    assert snapshot["database"] == {
        "backend_intent": "sqlite",
        "database_url_configured": False,
        "postgres_url_configured": False,
        "turso_url_configured": False,
        "turso_auth_token_configured": False,
        "remote_database_configured": False,
    }
    assert snapshot["stripe_key_mode"] == "missing"
    assert snapshot["stripe_catalog_env_configured"] is False
    assert snapshot["stripe_pricing_version_reconciled"] is False
    assert snapshot["stripe_sandbox_ready"] is False
    assert snapshot["google_ads_developer_token_configured"] is False
    assert snapshot["google_ads_login_customer_id_configured"] is False
    assert snapshot["privacy_controls"] == {
        "connector_disconnect": True,
        "scoped_synced_history_deletion": True,
        "account_deletion_backend": True,
        "full_account_deletion": True,
    }
    assert snapshot["pilot_readiness"]["configuration_ready"] is False
    assert snapshot["pilot_readiness"]["configuration_blockers"] == [
        "core_internal_secrets_configured",
        "remote_database_configured",
        "stripe_sandbox_ready",
        "google_oauth_configured",
        "google_ads_api_configured",
        "meta_oauth_configured",
        "transactional_email_configured",
    ]


def test_beta_readiness_prefers_postgres_intent_over_turso_compat_alias(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-placeholder")
    monkeypatch.setenv("TURSO_DATABASE_URL", "postgresql://compat-placeholder")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["database"] == {
        "backend_intent": "postgres",
        "database_url_configured": True,
        "postgres_url_configured": False,
        "turso_url_configured": True,
        "turso_auth_token_configured": False,
        "remote_database_configured": True,
    }


def test_beta_readiness_reports_legacy_turso_without_exposing_url(monkeypatch):
    _clear(monkeypatch)
    secret_url = "libsql://private-beta-secret.invalid"
    secret_token = "private-turso-auth-token"
    monkeypatch.setenv("TURSO_DATABASE_URL", secret_url)
    monkeypatch.setenv("TURSO_AUTH_TOKEN", secret_token)
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["database"]["backend_intent"] == "turso"
    assert snapshot["database"]["turso_auth_token_configured"] is True
    assert snapshot["database"]["remote_database_configured"] is True
    assert secret_url not in str(snapshot)
    assert secret_token not in str(snapshot)


def test_beta_readiness_detects_unsafe_execution_flags(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_EXECUTION_ENABLED", "true")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["external_execution_enabled"] is True
    assert snapshot["private_beta_execution_safe"] is False
    assert "execution_locked" in snapshot["pilot_readiness"]["configuration_blockers"]


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
    assert "production_transport_safe" in snapshot["pilot_readiness"]["configuration_blockers"]


def test_beta_readiness_accepts_secure_production_transport(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["production_transport_safe"] is True
    assert snapshot["transport"]["app_url_https"] is True
    assert snapshot["transport"]["secure_cookie_explicitly_disabled"] is False


def test_beta_readiness_marks_current_stripe_sandbox_ready(monkeypatch):
    _clear(monkeypatch)
    _set_current_stripe_sandbox(monkeypatch)

    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["stripe_key_mode"] == "test"
    assert snapshot["stripe_catalog_env_configured"] is True
    assert snapshot["stripe_pricing_version_reconciled"] is True
    assert snapshot["stripe_webhook_env_configured"] is True
    assert snapshot["stripe_sandbox_ready"] is True


def test_beta_readiness_rejects_live_key_or_wrong_pricing_version(monkeypatch):
    _clear(monkeypatch)
    _set_current_stripe_sandbox(monkeypatch, key="sk_live_private")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["stripe_key_mode"] == "live"
    assert snapshot["stripe_sandbox_ready"] is False

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", "old-model")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["stripe_pricing_version_reconciled"] is False
    assert snapshot["stripe_sandbox_ready"] is False


def test_beta_readiness_marks_google_ads_api_config_incomplete_without_developer_token(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client-private")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret-private")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://example.test/google")

    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["google_oauth_configured"] is True
    assert snapshot["google_ads_developer_token_configured"] is False
    assert snapshot["pilot_readiness"]["checks"]["google_ads_api_configured"] is False
    assert "google_ads_api_configured" in snapshot["pilot_readiness"]["configuration_blockers"]


def test_beta_readiness_marks_configuration_ready_without_claiming_manual_gates(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "configured-value-a")
    monkeypatch.setenv("CRON_SECRET", "configured-value-b")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-placeholder")
    _set_current_stripe_sandbox(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client-private")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret-private")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://example.test/google")
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "google-ads-private")
    monkeypatch.setenv("META_APP_ID", "meta-app-private")
    monkeypatch.setenv("META_APP_SECRET", "meta-secret-private")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.test/meta")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "sender@example.test")

    snapshot = beta_readiness.beta_safety_snapshot()
    pilot = snapshot["pilot_readiness"]
    assert pilot["configuration_ready"] is True
    assert pilot["configuration_blockers"] == []
    assert pilot["checks"]["execution_locked"] is True
    assert pilot["checks"]["core_internal_secrets_configured"] is True
    assert pilot["checks"]["google_ads_api_configured"] is True
    assert pilot["manual_gates"] == [
        "production_observability_verified",
        "final_authenticated_browser_qa",
        "privacy_terms_legal_review",
        "google_ads_external_approval_and_manager_link_if_required",
        "google_ads_live_read_only_sync_verified",
        "meta_ads_live_read_only_sync_verified",
        "fresh_stripe_sandbox_end_to_end_test",
    ]


def test_pricing_reconciliation_requires_exact_current_marker(monkeypatch):
    _clear(monkeypatch)
    _set_current_stripe_sandbox(monkeypatch)
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", "legacy")
    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["stripe_pricing_version_reconciled"] is False
    assert snapshot["stripe_sandbox_ready"] is False
    assert any("pricing-version marker" in note.lower() for note in snapshot["notes"])


def test_beta_readiness_endpoint_never_returns_secret_values(monkeypatch):
    _clear(monkeypatch)
    values = {
        "VEZMORA_SECRET_KEY": "configured-value-a",
        "CRON_SECRET": "configured-value-b",
        "VEZMORA_APP_URL": "https://example.test",
        "DATABASE_URL": "postgresql://database-private",
        "STRIPE_SECRET_KEY": "sk_test_private",
        "STRIPE_WEBHOOK_SECRET": "whsec_private",
        "STRIPE_PRICE_START": "price_start_private",
        "STRIPE_PRICE_GROWTH": "price_growth_private",
        "STRIPE_PRICE_PRO": "price_pro_private",
        "VEZMORA_STRIPE_PRICING_VERSION": CURRENT_PRICING_VERSION,
        "GOOGLE_CLIENT_ID": "google-client-private",
        "GOOGLE_CLIENT_SECRET": "google-secret-private",
        "GOOGLE_REDIRECT_URI": "https://example.test/google",
        "GOOGLE_ADS_DEVELOPER_TOKEN": "google-ads-private",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "1234567890",
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
    assert payload["database"]["backend_intent"] == "postgres"
    assert payload["database"]["database_url_configured"] is True
    assert payload["database"]["turso_url_configured"] is False
    assert payload["stripe_catalog_env_configured"] is True
    assert payload["stripe_pricing_version_reconciled"] is True
    assert payload["stripe_webhook_env_configured"] is True
    assert payload["stripe_key_mode"] == "test"
    assert payload["stripe_sandbox_ready"] is True
    assert payload["google_oauth_configured"] is True
    assert payload["google_ads_developer_token_configured"] is True
    assert payload["google_ads_login_customer_id_configured"] is True
    assert payload["pilot_readiness"]["checks"]["google_ads_api_configured"] is True
    assert payload["pilot_readiness"]["checks"]["core_internal_secrets_configured"] is True
    assert payload["meta_oauth_configured"] is True
    assert payload["smtp_minimum_configured"] is True
    assert payload["production_transport_safe"] is True
    assert payload["privacy_controls"]["account_deletion_backend"] is True
    assert payload["privacy_controls"]["full_account_deletion"] is True
    assert payload["pilot_readiness"]["configuration_ready"] is True

    rendered = response.text
    for secret in values.values():
        if secret == CURRENT_PRICING_VERSION:
            # The expected version identifier is intentionally public metadata.
            continue
        assert secret not in rendered
