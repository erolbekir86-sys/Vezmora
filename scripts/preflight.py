from __future__ import annotations

import json
import os
import sys
from typing import Any

CORE_REQUIRED = [
    "VEZMORA_APP_URL",
    "VEZMORA_SECRET_KEY",
    "OPENAI_API_KEY",
    "CRON_SECRET",
]

BILLING = [
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRICE_STARTER",
    "STRIPE_PRICE_GROWTH",
    "STRIPE_PRICE_SCALE",
]

VERIFIED_STRIPE_SANDBOX_PRICES = {
    "STRIPE_PRICE_STARTER": "price_1UCGVX32EFR9j6MxSP6VB2TF",
    "STRIPE_PRICE_GROWTH": "price_1UCGVf32EFR9j6Mx0fCKTHzK",
    "STRIPE_PRICE_SCALE": "price_1UCGVm32EFR9j6MxFOxJD3zp",
}

SMTP = ["SMTP_HOST", "SMTP_FROM"]
GOOGLE_OAUTH = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]
META_OAUTH = ["META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"]

# These flags must remain false during the private beta. The preflight treats an
# accidental enablement as a safety failure rather than merely informational.
BETA_LOCKED_FLAGS = [
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
    "VEZMORA_DEV_SHOW_TOKENS",
]


def configured(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def enabled(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def database_configured() -> bool:
    # Production prefers Neon/Postgres. Keep the legacy Turso pair supported
    # for compatibility with older deployments.
    if configured("DATABASE_URL") or configured("POSTGRES_URL"):
        return True
    return configured("TURSO_DATABASE_URL") and configured("TURSO_AUTH_TOKEN")


def _missing(names: list[str]) -> list[str]:
    return [name for name in names if not configured(name)]


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


def build_report() -> dict[str, Any]:
    core_missing = _missing(CORE_REQUIRED)
    if not database_configured():
        core_missing.append("DATABASE_URL/POSTGRES_URL (or legacy TURSO_DATABASE_URL + TURSO_AUTH_TOKEN)")

    billing_missing = _missing(BILLING)
    smtp_missing = _missing(SMTP)
    google_oauth_missing = _missing(GOOGLE_OAUTH)
    meta_oauth_missing = _missing(META_OAUTH)
    unsafe_flags = [name for name in BETA_LOCKED_FLAGS if enabled(name)]

    app_url = (os.getenv("VEZMORA_APP_URL") or "").strip().lower()
    production_like = enabled("VERCEL") or (os.getenv("VERCEL_ENV") or "").strip().lower() == "production"
    insecure_app_url = bool(production_like and app_url and not app_url.startswith("https://"))
    insecure_cookie_override = bool(production_like and configured("VEZMORA_COOKIE_SECURE") and not enabled("VEZMORA_COOKIE_SECURE"))

    beta_execution_locked = not unsafe_flags
    production_transport_safe = not insecure_app_url and not insecure_cookie_override
    stripe_key_mode = _stripe_key_mode()
    stripe_catalog_matches = _stripe_catalog_matches_verified_sandbox()
    stripe_sandbox_ready = (
        stripe_key_mode == "test"
        and configured("STRIPE_WEBHOOK_SECRET")
        and stripe_catalog_matches
    )
    google_oauth_ready = not google_oauth_missing
    meta_oauth_ready = not meta_oauth_missing
    smtp_ready = not smtp_missing

    pilot_checks = {
        "execution_locked": beta_execution_locked,
        "production_transport_safe": production_transport_safe,
        "remote_database_configured": database_configured(),
        "stripe_sandbox_ready": stripe_sandbox_ready,
        "google_oauth_configured": google_oauth_ready,
        "meta_oauth_configured": meta_oauth_ready,
        "transactional_email_configured": smtp_ready,
    }
    pilot_blockers = [name for name, ready in pilot_checks.items() if not ready]

    return {
        "brand": "Vexmera",
        "phase": "private_beta",
        "core_ready": not core_missing,
        "database_ready": database_configured(),
        # Kept for deployment-config compatibility: all billing variables exist.
        # Use stripe_sandbox_ready for the stricter private-beta go/no-go check.
        "billing_ready": not billing_missing,
        "stripe_key_mode": stripe_key_mode,
        "stripe_catalog_matches_verified_sandbox": stripe_catalog_matches,
        "stripe_sandbox_ready": stripe_sandbox_ready,
        "smtp_ready": smtp_ready,
        "google_oauth_ready": google_oauth_ready,
        "google_ads_developer_token_ready": configured("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "google_ads_login_customer_id_ready": configured("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "meta_oauth_ready": meta_oauth_ready,
        "serverless_enabled": enabled("VEZMORA_SERVERLESS"),
        "beta_execution_locked": beta_execution_locked,
        "production_transport_safe": production_transport_safe,
        "pilot_readiness": {
            "configuration_ready": not pilot_blockers,
            "checks": pilot_checks,
            "configuration_blockers": pilot_blockers,
            "manual_gates": [
                "final_authenticated_browser_qa",
                "privacy_terms_legal_review",
                "google_ads_external_approval_and_manager_link_if_required",
                "fresh_stripe_sandbox_end_to_end_test",
            ],
        },
        "missing": {
            "core": core_missing,
            "billing": billing_missing,
            "smtp": smtp_missing,
            "google_oauth": google_oauth_missing,
            "meta_oauth": meta_oauth_missing,
        },
        "unsafe_beta_flags": unsafe_flags,
        "transport_issues": [
            issue
            for issue, active in (
                ("VEZMORA_APP_URL must use https in production", insecure_app_url),
                ("VEZMORA_COOKIE_SECURE must not be disabled in production", insecure_cookie_override),
            )
            if active
        ],
    }


def _status(value: bool) -> str:
    return "READY" if value else "MISSING CONFIG"


def print_report(report: dict[str, Any]) -> None:
    print("Vexmera deployment preflight")
    print(f"phase: {report['phase']}")
    print(f"core: {_status(bool(report['core_ready']))}")
    print(f"database: {_status(bool(report['database_ready']))}")
    print(f"billing variables: {_status(bool(report['billing_ready']))}")
    print(f"Stripe sandbox: {'READY' if report['stripe_sandbox_ready'] else 'NOT READY'}")
    print(f"transactional email: {_status(bool(report['smtp_ready']))}")
    print(f"Google OAuth: {_status(bool(report['google_oauth_ready']))}")
    print(f"Google Ads developer token: {_status(bool(report['google_ads_developer_token_ready']))}")
    print(f"Google Ads manager login ID: {_status(bool(report['google_ads_login_customer_id_ready']))}")
    print(f"Meta OAuth: {_status(bool(report['meta_oauth_ready']))}")
    print(f"serverless mode enabled: {bool(report['serverless_enabled'])}")
    print(f"private-beta execution locks: {'SAFE' if report['beta_execution_locked'] else 'UNSAFE'}")
    print(f"production transport: {'SAFE' if report['production_transport_safe'] else 'UNSAFE'}")
    pilot = report["pilot_readiness"]
    print(f"pilot configuration: {'READY' if pilot['configuration_ready'] else 'BLOCKED'}")
    print(
        "Pilot configuration blockers:",
        ", ".join(pilot["configuration_blockers"]) if pilot["configuration_blockers"] else "none",
    )

    missing = report["missing"]
    for group in ("core", "billing", "smtp", "google_oauth", "meta_oauth"):
        values = missing[group]
        print(f"Missing {group} variables:", ", ".join(values) if values else "none")
    print(
        "Unsafe beta flags:",
        ", ".join(report["unsafe_beta_flags"]) if report["unsafe_beta_flags"] else "none",
    )
    print(
        "Transport issues:",
        "; ".join(report["transport_issues"]) if report["transport_issues"] else "none",
    )
    print("Secret values are intentionally never printed.")
    print("Pilot configuration readiness does not replace the listed manual gates.")


def main() -> int:
    report = build_report()
    if "--json" in sys.argv[1:]:
        # The report contains names, booleans, safe modes and non-secret readiness
        # labels only. It never contains environment-variable secret values.
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)
    return 1 if (
        not report["core_ready"]
        or not report["beta_execution_locked"]
        or not report["production_transport_safe"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
