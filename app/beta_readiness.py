from __future__ import annotations

import os

from .main import app as _app
from .pricing import CURRENT_PRICING_VERSION, STRIPE_PRICE_ENV, checkout_pricing_reconciled


def _configured(name: str) -> bool:
    return bool((os.getenv(name) or "").strip())


def _enabled(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _all_configured(*names: str) -> bool:
    return all(_configured(name) for name in names)


def _production_like() -> bool:
    return _enabled("VERCEL") or (os.getenv("VERCEL_ENV") or "").strip().lower() == "production"


def _smtp_starttls_enabled() -> bool:
    raw = os.getenv("SMTP_STARTTLS")
    if raw is None:
        return True
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _transport_snapshot() -> dict[str, object]:
    app_url = (os.getenv("VEZMORA_APP_URL") or "").strip().lower()
    production_like = _production_like()
    app_url_https = bool(app_url.startswith("https://")) if app_url else False
    cookie_secure_override = None
    if _configured("VEZMORA_COOKIE_SECURE"):
        cookie_secure_override = _enabled("VEZMORA_COOKIE_SECURE")

    smtp_minimum_configured = _all_configured("SMTP_HOST", "SMTP_FROM")
    smtp_starttls_disabled = smtp_minimum_configured and not _smtp_starttls_enabled()

    safe = True
    if production_like:
        safe = (
            app_url_https
            and cookie_secure_override is not False
            and not smtp_starttls_disabled
        )

    return {
        "production_like": production_like,
        "app_url_configured": bool(app_url),
        "app_url_https": app_url_https,
        "secure_cookie_explicitly_disabled": cookie_secure_override is False,
        "smtp_starttls_required_but_disabled": bool(production_like and smtp_starttls_disabled),
        "safe": safe,
    }


def _database_snapshot() -> dict[str, object]:
    """Report non-secret database intent without exposing connection strings."""
    database_url_configured = _configured("DATABASE_URL")
    postgres_url_configured = _configured("POSTGRES_URL")
    turso_url_configured = _configured("TURSO_DATABASE_URL")

    if database_url_configured or postgres_url_configured:
        backend_intent = "postgres"
    elif turso_url_configured:
        backend_intent = "turso"
    else:
        backend_intent = "sqlite"

    return {
        "backend_intent": backend_intent,
        "database_url_configured": database_url_configured,
        "postgres_url_configured": postgres_url_configured,
        "turso_url_configured": turso_url_configured,
        "remote_database_configured": database_url_configured or postgres_url_configured or turso_url_configured,
    }


def _stripe_key_mode() -> str:
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        return "missing"
    if key.startswith(("sk_test_", "rk_test_")):
        return "test"
    if key.startswith(("sk_live_", "rk_live_")):
        return "live"
    return "unknown"


def _pilot_readiness_snapshot(
    *,
    private_beta_execution_safe: bool,
    production_transport_safe: bool,
    core_internal_secrets_configured: bool,
    remote_database_configured: bool,
    stripe_sandbox_ready: bool,
    google_oauth_configured: bool,
    google_ads_api_configured: bool,
    meta_oauth_configured: bool,
    smtp_ready: bool,
) -> dict[str, object]:
    """Summarize configuration-only blockers for the five-company pilot."""
    checks = {
        "execution_locked": private_beta_execution_safe,
        "production_transport_safe": production_transport_safe,
        "core_internal_secrets_configured": core_internal_secrets_configured,
        "remote_database_configured": remote_database_configured,
        "stripe_sandbox_ready": stripe_sandbox_ready,
        "google_oauth_configured": google_oauth_configured,
        "google_ads_api_configured": google_ads_api_configured,
        "meta_oauth_configured": meta_oauth_configured,
        "transactional_email_configured": smtp_ready,
    }
    blockers = [name for name, ready in checks.items() if not ready]
    return {
        "configuration_ready": not blockers,
        "checks": checks,
        "configuration_blockers": blockers,
        "manual_gates": [
            "production_observability_verified",
            "final_authenticated_browser_qa",
            "privacy_terms_legal_review",
            "google_ads_external_approval_and_manager_link_if_required",
            "google_ads_live_read_only_sync_verified",
            "meta_ads_live_read_only_sync_verified",
            "fresh_stripe_sandbox_end_to_end_test",
        ],
    }


def beta_safety_snapshot() -> dict[str, object]:
    execution_enabled = _enabled("VEZMORA_EXECUTION_ENABLED")
    autopilot_execution_enabled = _enabled("VEZMORA_AUTOPILOT_EXECUTION_ENABLED")
    meta_execution_scope_enabled = _enabled("VEZMORA_ENABLE_META_EXECUTION_SCOPE")
    dev_show_tokens_enabled = _enabled("VEZMORA_DEV_SHOW_TOKENS")
    private_beta_execution_safe = not (
        execution_enabled
        or autopilot_execution_enabled
        or meta_execution_scope_enabled
        or dev_show_tokens_enabled
    )
    transport = _transport_snapshot()
    production_like = bool(transport["production_like"])
    core_internal_secrets_configured = _all_configured("VEZMORA_SECRET_KEY", "CRON_SECRET")
    database = _database_snapshot()
    stripe_key_mode = _stripe_key_mode()
    stripe_catalog_configured = _all_configured(*STRIPE_PRICE_ENV.values())
    stripe_pricing_version_reconciled = checkout_pricing_reconciled()
    stripe_webhook_configured = _configured("STRIPE_WEBHOOK_SECRET")
    stripe_sandbox_ready = (
        stripe_key_mode == "test"
        and stripe_catalog_configured
        and stripe_pricing_version_reconciled
        and stripe_webhook_configured
    )
    google_oauth_configured = _all_configured(
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
    )
    google_ads_developer_token_configured = _configured("GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_login_customer_id_configured = _configured("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    meta_oauth_configured = _all_configured(
        "META_APP_ID",
        "META_APP_SECRET",
        "META_REDIRECT_URI",
    )
    smtp_minimum_configured = _all_configured("SMTP_HOST", "SMTP_FROM")
    smtp_transport_ready = smtp_minimum_configured and (
        not production_like or _smtp_starttls_enabled()
    )

    pilot_readiness = _pilot_readiness_snapshot(
        private_beta_execution_safe=private_beta_execution_safe,
        production_transport_safe=bool(transport["safe"]),
        core_internal_secrets_configured=core_internal_secrets_configured,
        remote_database_configured=bool(database["remote_database_configured"]),
        stripe_sandbox_ready=stripe_sandbox_ready,
        google_oauth_configured=google_oauth_configured,
        google_ads_api_configured=google_ads_developer_token_configured,
        meta_oauth_configured=meta_oauth_configured,
        smtp_ready=smtp_transport_ready,
    )

    return {
        "ok": True,
        "brand": "Vexmera",
        "phase": "private_beta",
        "external_execution_enabled": execution_enabled,
        "autopilot_execution_enabled": autopilot_execution_enabled,
        "meta_execution_scope_enabled": meta_execution_scope_enabled,
        "dev_show_tokens_enabled": dev_show_tokens_enabled,
        "private_beta_execution_safe": private_beta_execution_safe,
        "production_transport_safe": bool(transport["safe"]),
        "core_internal_secrets_configured": core_internal_secrets_configured,
        "transport": transport,
        "database": database,
        "stripe_key_mode": stripe_key_mode,
        "stripe_catalog_env_configured": stripe_catalog_configured,
        "stripe_pricing_version_reconciled": stripe_pricing_version_reconciled,
        "stripe_expected_pricing_version": CURRENT_PRICING_VERSION,
        "stripe_webhook_env_configured": stripe_webhook_configured,
        "stripe_sandbox_ready": stripe_sandbox_ready,
        "google_oauth_configured": google_oauth_configured,
        "google_ads_developer_token_configured": google_ads_developer_token_configured,
        "google_ads_login_customer_id_configured": google_ads_login_customer_id_configured,
        "meta_oauth_configured": meta_oauth_configured,
        "smtp_minimum_configured": smtp_minimum_configured,
        "smtp_transport_ready": smtp_transport_ready,
        "privacy_controls": {
            "connector_disconnect": True,
            "scoped_synced_history_deletion": True,
            "account_deletion_backend": True,
            "full_account_deletion": True,
        },
        "pilot_readiness": pilot_readiness,
        "notes": [
            "Configuration booleans do not prove third-party approval or account access.",
            "Core internal-secret diagnostics report only whether OAuth-token encryption and maintenance-endpoint secrets are configured; values are never returned.",
            "Database readiness reports only backend intent and configured-variable booleans; connection strings are never returned.",
            "Stripe readiness requires test mode, all current Start/Growth/Pro price variables, the webhook secret, and the exact pricing-version marker; no Stripe identifiers are returned.",
            "The pricing-version marker must only be set after the current Stripe sandbox catalog has been verified against the public prices.",
            "Transactional email readiness requires minimum SMTP configuration and, in production, STARTTLS must not be disabled.",
            "Pilot readiness is configuration-only; production observability, live read-only connector verification and other manual gates remain required before external onboarding.",
            "Google Ads configuration readiness requires OAuth and a developer token; manager/login-customer linking remains a separate external/manual gate because it depends on account topology.",
            "Account deletion is self-service but deliberately blocked until shared ownership and active subscription constraints are resolved.",
            "Google Ads Basic Access and manager linking require separate external verification.",
            "Live billing, VAT/tax, legal terms and canonical production domain remain separate launch decisions.",
        ],
    }


def _public_beta_safety_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    """Expose only the public execution-lock evidence needed by live preflight checks.

    Detailed configuration diagnostics remain available to local/operator tooling via
    beta_safety_snapshot(), but production callers do not need an inventory of which
    database, billing, OAuth, SMTP, or internal-secret settings are configured.
    """
    public_keys = (
        "ok",
        "brand",
        "phase",
        "external_execution_enabled",
        "autopilot_execution_enabled",
        "meta_execution_scope_enabled",
        "dev_show_tokens_enabled",
        "private_beta_execution_safe",
        "production_transport_safe",
    )
    return {key: snapshot[key] for key in public_keys}


@_app.get("/health/beta-readiness")
def beta_readiness() -> dict[str, object]:
    """Return minimal production safety evidence and fuller local diagnostics."""
    snapshot = beta_safety_snapshot()
    if _production_like():
        return _public_beta_safety_snapshot(snapshot)
    return snapshot
