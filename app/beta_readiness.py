from __future__ import annotations

import os

from .main import app as _app


VERIFIED_STRIPE_SANDBOX_PRICES = {
    "STRIPE_PRICE_STARTER": "price_1UCGVX32EFR9j6MxSP6VB2TF",
    "STRIPE_PRICE_GROWTH": "price_1UCGVf32EFR9j6Mx0fCKTHzK",
    "STRIPE_PRICE_SCALE": "price_1UCGVm32EFR9j6MxFOxJD3zp",
}


def _configured(name: str) -> bool:
    return bool((os.getenv(name) or "").strip())


def _enabled(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _all_configured(*names: str) -> bool:
    return all(_configured(name) for name in names)


def _production_like() -> bool:
    return _enabled("VERCEL") or (os.getenv("VERCEL_ENV") or "").strip().lower() == "production"


def _transport_snapshot() -> dict[str, object]:
    app_url = (os.getenv("VEZMORA_APP_URL") or "").strip().lower()
    production_like = _production_like()
    app_url_https = bool(app_url.startswith("https://")) if app_url else False
    cookie_secure_override = None
    if _configured("VEZMORA_COOKIE_SECURE"):
        cookie_secure_override = _enabled("VEZMORA_COOKIE_SECURE")

    safe = True
    if production_like:
        safe = app_url_https and cookie_secure_override is not False

    return {
        "production_like": production_like,
        "app_url_configured": bool(app_url),
        "app_url_https": app_url_https,
        "secure_cookie_explicitly_disabled": cookie_secure_override is False,
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


def _stripe_catalog_matches_verified_sandbox() -> bool:
    return all((os.getenv(name) or "").strip() == expected for name, expected in VERIFIED_STRIPE_SANDBOX_PRICES.items())


def beta_safety_snapshot() -> dict[str, object]:
    execution_enabled = _enabled("VEZMORA_EXECUTION_ENABLED")
    autopilot_execution_enabled = _enabled("VEZMORA_AUTOPILOT_EXECUTION_ENABLED")
    meta_execution_scope_enabled = _enabled("VEZMORA_ENABLE_META_EXECUTION_SCOPE")
    dev_show_tokens_enabled = _enabled("VEZMORA_DEV_SHOW_TOKENS")
    transport = _transport_snapshot()
    database = _database_snapshot()
    stripe_key_mode = _stripe_key_mode()
    stripe_catalog_configured = _all_configured(*VERIFIED_STRIPE_SANDBOX_PRICES.keys())
    stripe_catalog_matches = _stripe_catalog_matches_verified_sandbox()
    stripe_webhook_configured = _configured("STRIPE_WEBHOOK_SECRET")

    return {
        "ok": True,
        "brand": "Vexmera",
        "phase": "private_beta",
        "external_execution_enabled": execution_enabled,
        "autopilot_execution_enabled": autopilot_execution_enabled,
        "meta_execution_scope_enabled": meta_execution_scope_enabled,
        "dev_show_tokens_enabled": dev_show_tokens_enabled,
        "private_beta_execution_safe": not (
            execution_enabled
            or autopilot_execution_enabled
            or meta_execution_scope_enabled
            or dev_show_tokens_enabled
        ),
        "production_transport_safe": bool(transport["safe"]),
        "transport": transport,
        "database": database,
        "stripe_key_mode": stripe_key_mode,
        "stripe_catalog_env_configured": stripe_catalog_configured,
        "stripe_catalog_matches_verified_sandbox": stripe_catalog_matches,
        "stripe_webhook_env_configured": stripe_webhook_configured,
        "stripe_sandbox_ready": (
            stripe_key_mode == "test"
            and stripe_catalog_matches
            and stripe_webhook_configured
        ),
        "google_oauth_configured": _all_configured(
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
        ),
        "google_ads_developer_token_configured": _configured("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "google_ads_login_customer_id_configured": _configured("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "meta_oauth_configured": _all_configured(
            "META_APP_ID",
            "META_APP_SECRET",
            "META_REDIRECT_URI",
        ),
        "smtp_minimum_configured": _all_configured("SMTP_HOST", "SMTP_FROM"),
        "privacy_controls": {
            "connector_disconnect": True,
            "scoped_synced_history_deletion": True,
            "account_deletion_backend": True,
            "full_account_deletion": True,
        },
        "notes": [
            "Configuration booleans do not prove third-party approval or account access.",
            "Database readiness reports only backend intent and configured-variable booleans; connection strings are never returned.",
            "Stripe sandbox readiness compares environment configuration with the verified Vexmera test catalog without exposing keys or Price IDs.",
            "Account deletion is self-service but deliberately blocked until shared ownership and active subscription constraints are resolved.",
            "Google Ads Basic Access and manager linking require separate external verification.",
            "Live billing, VAT/tax, legal terms and canonical production domain remain separate launch decisions.",
        ],
    }


@_app.get("/health/beta-readiness")
def beta_readiness() -> dict[str, object]:
    """Safe, non-secret private-beta readiness and execution-lock diagnostics."""
    return beta_safety_snapshot()
