from __future__ import annotations

from scripts import preflight


def _clear(monkeypatch):
    names = set(
        preflight.CORE_REQUIRED
        + preflight.BILLING
        + preflight.SMTP
        + preflight.GOOGLE_OAUTH
        + preflight.META_OAUTH
        + preflight.BETA_LOCKED_FLAGS
        + [
            "DATABASE_URL",
            "POSTGRES_URL",
            "TURSO_DATABASE_URL",
            "TURSO_AUTH_TOKEN",
            "GOOGLE_ADS_DEVELOPER_TOKEN",
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
            "VEZMORA_SERVERLESS",
            "VEZMORA_COOKIE_SECURE",
            "SMTP_STARTTLS",
            "VERCEL",
            "VERCEL_ENV",
        ]
    )
    for name in names:
        monkeypatch.delenv(name, raising=False)


def test_preflight_report_is_safe_and_marks_beta_execution_locked(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "never-print-this-app-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "never-print-this-openai-key")
    monkeypatch.setenv("CRON_SECRET", "never-print-this-cron-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret:secret@example.test/db")

    report = preflight.build_report()
    assert report["core_ready"] is True
    assert report["database_ready"] is True
    assert report["beta_execution_locked"] is True
    assert report["production_transport_safe"] is True
    assert report["unsafe_beta_flags"] == []
    assert report["transport_issues"] == []
    serialized = str(report)
    assert "never-print-this" not in serialized
    assert "postgresql://" not in serialized


def test_preflight_detects_accidentally_enabled_execution_and_dev_tokens(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("VEZMORA_ENABLE_META_EXECUTION_SCOPE", "yes")
    monkeypatch.setenv("VEZMORA_DEV_SHOW_TOKENS", "on")

    report = preflight.build_report()
    assert report["beta_execution_locked"] is False
    assert report["unsafe_beta_flags"] == [
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
        "VEZMORA_DEV_SHOW_TOKENS",
    ]
    assert "execution_locked" in report["pilot_readiness"]["configuration_blockers"]


def test_preflight_rejects_insecure_production_transport(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "http://example.test")
    monkeypatch.setenv("VEZMORA_COOKIE_SECURE", "false")

    report = preflight.build_report()
    assert report["production_transport_safe"] is False
    assert report["transport_issues"] == [
        "VEZMORA_APP_URL must use https in production",
        "VEZMORA_COOKIE_SECURE must not be disabled in production",
    ]
    assert "production_transport_safe" in report["pilot_readiness"]["configuration_blockers"]


def test_preflight_rejects_plaintext_smtp_in_production(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("VEZMORA_COOKIE_SECURE", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.test")
    monkeypatch.setenv("SMTP_STARTTLS", "false")

    report = preflight.build_report()
    assert report["smtp_ready"] is False
    assert report["production_transport_safe"] is False
    assert report["transport_issues"] == ["SMTP_STARTTLS must not be disabled in production"]
    assert "production_transport_safe" in report["pilot_readiness"]["configuration_blockers"]
    assert "transactional_email_configured" in report["pilot_readiness"]["configuration_blockers"]


def test_preflight_allows_secure_production_transport(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("VEZMORA_COOKIE_SECURE", "true")

    report = preflight.build_report()
    assert report["production_transport_safe"] is True
    assert report["transport_issues"] == []


def test_preflight_pilot_requires_internal_secrets(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("OPENAI_API_KEY", "configured")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-connection")
    for name in preflight.SMTP + preflight.GOOGLE_OAUTH + preflight.META_OAUTH:
        monkeypatch.setenv(name, "configured")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", preflight.CURRENT_PRICING_VERSION)
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "configured")

    report = preflight.build_report()
    assert report["pilot_readiness"]["configuration_ready"] is False
    assert "core_internal_secrets_configured" in report["pilot_readiness"]["configuration_blockers"]


def test_preflight_pilot_accepts_cloud_managed_ads_without_developer_token(monkeypatch):
    _clear(monkeypatch)
    for name in preflight.CORE_REQUIRED:
        monkeypatch.setenv(name, "configured")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-connection")
    for name in preflight.SMTP + preflight.GOOGLE_OAUTH + preflight.META_OAUTH:
        monkeypatch.setenv(name, "configured")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", preflight.CURRENT_PRICING_VERSION)

    report = preflight.build_report()
    assert report["google_ads_developer_token_ready"] is False
    assert report["pilot_readiness"]["configuration_ready"] is True
    assert "google_ads_api_configured" not in report["pilot_readiness"]["configuration_blockers"]


def test_preflight_reports_optional_service_readiness_without_secret_values(monkeypatch, capsys):
    _clear(monkeypatch)
    for name in preflight.CORE_REQUIRED:
        monkeypatch.setenv(name, f"secret-{name}")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-connection")
    for name in preflight.SMTP + preflight.GOOGLE_OAUTH + preflight.META_OAUTH:
        monkeypatch.setenv(name, f"secret-{name}")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", preflight.CURRENT_PRICING_VERSION)
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "secret-developer-token")
    monkeypatch.setenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "1234567890")

    report = preflight.build_report()
    assert report["billing_ready"] is True
    assert report["stripe_key_mode"] == "test"
    assert report["stripe_current_price_env_configured"] is True
    assert report["stripe_pricing_version_reconciled"] is True
    assert report["stripe_sandbox_ready"] is True
    assert report["smtp_ready"] is True
    assert report["google_oauth_ready"] is True
    assert report["google_ads_developer_token_ready"] is True
    assert report["google_ads_login_customer_id_ready"] is True
    assert report["meta_oauth_ready"] is True
    assert report["pilot_readiness"]["configuration_ready"] is True
    assert report["pilot_readiness"]["configuration_blockers"] == []
    assert "production_observability_verified" in report["pilot_readiness"]["manual_gates"]

    preflight.print_report(report)
    output = capsys.readouterr().out
    assert "secret-" not in output
    assert "postgresql://" not in output
    assert "private-beta execution locks: SAFE" in output
    assert "production transport: SAFE" in output
    assert "current pricing model: RECONCILED" in output
    assert "Stripe sandbox: READY" in output
    assert "pilot configuration: READY" in output


def test_preflight_requires_exact_pricing_version_marker(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", "old-model")

    report = preflight.build_report()
    assert report["stripe_current_price_env_configured"] is True
    assert report["stripe_pricing_version_reconciled"] is False
    assert report["stripe_sandbox_ready"] is False


def test_preflight_does_not_treat_merely_present_live_stripe_config_as_sandbox_ready(monkeypatch):
    _clear(monkeypatch)
    for name in preflight.CORE_REQUIRED:
        monkeypatch.setenv(name, "configured")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-connection")
    for name in preflight.SMTP + preflight.GOOGLE_OAUTH + preflight.META_OAUTH:
        monkeypatch.setenv(name, "configured")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_private")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", preflight.CURRENT_PRICING_VERSION)
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "configured")

    report = preflight.build_report()
    assert report["billing_ready"] is True
    assert report["stripe_key_mode"] == "live"
    assert report["stripe_sandbox_ready"] is False
    assert report["pilot_readiness"]["configuration_ready"] is False
    assert "stripe_sandbox_ready" in report["pilot_readiness"]["configuration_blockers"]
