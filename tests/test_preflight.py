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
            "VEZMORA_SERVERLESS",
            "VEZMORA_COOKIE_SECURE",
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


def test_preflight_allows_secure_production_transport(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://example.test")
    monkeypatch.setenv("VEZMORA_COOKIE_SECURE", "true")

    report = preflight.build_report()
    assert report["production_transport_safe"] is True
    assert report["transport_issues"] == []


def test_preflight_reports_optional_service_readiness_without_secret_values(monkeypatch, capsys):
    _clear(monkeypatch)
    for name in preflight.CORE_REQUIRED:
        monkeypatch.setenv(name, f"secret-{name}")
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-connection")
    for name in preflight.BILLING + preflight.SMTP + preflight.GOOGLE_OAUTH + preflight.META_OAUTH:
        monkeypatch.setenv(name, f"secret-{name}")
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "secret-developer-token")

    report = preflight.build_report()
    assert report["billing_ready"] is True
    assert report["smtp_ready"] is True
    assert report["google_oauth_ready"] is True
    assert report["google_ads_developer_token_ready"] is True
    assert report["meta_oauth_ready"] is True

    preflight.print_report(report)
    output = capsys.readouterr().out
    assert "secret-" not in output
    assert "postgresql://" not in output
    assert "private-beta execution locks: SAFE" in output
    assert "production transport: SAFE" in output
