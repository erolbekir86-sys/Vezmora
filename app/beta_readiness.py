from __future__ import annotations

import os

from .main import app as _app


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


def beta_safety_snapshot() -> dict[str, object]:
    execution_enabled = _enabled("VEZMORA_EXECUTION_ENABLED")
    autopilot_execution_enabled = _enabled("VEZMORA_AUTOPILOT_EXECUTION_ENABLED")
    meta_execution_scope_enabled = _enabled("VEZMORA_ENABLE_META_EXECUTION_SCOPE")
    dev_show_tokens_enabled = _enabled("VEZMORA_DEV_SHOW_TOKENS")
    transport = _transport_snapshot()

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
        "stripe_catalog_env_configured": _all_configured(
            "STRIPE_PRICE_STARTER",
            "STRIPE_PRICE_GROWTH",
            "STRIPE_PRICE_SCALE",
        ),
        "stripe_webhook_env_configured": _configured("STRIPE_WEBHOOK_SECRET"),
        "google_oauth_configured": _all_configured(
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
        ),
        "google_ads_developer_token_configured": _configured("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "meta_oauth_configured": _all_configured(
            "META_APP_ID",
            "META_APP_SECRET",
            "META_REDIRECT_URI",
        ),
        "smtp_minimum_configured": _all_configured("SMTP_HOST", "SMTP_FROM"),
        "privacy_controls": {
            "connector_disconnect": True,
            "scoped_synced_history_deletion": True,
            "full_account_deletion": False,
        },
        "notes": [
            "Configuration booleans do not prove third-party approval or account access.",
            "Google Ads Basic Access and manager linking require separate external verification.",
            "Live billing, VAT/tax, legal terms and canonical production domain remain separate launch decisions.",
        ],
    }


@_app.get("/health/beta-readiness")
def beta_readiness() -> dict[str, object]:
    """Safe, non-secret private-beta readiness and execution-lock diagnostics."""
    return beta_safety_snapshot()
