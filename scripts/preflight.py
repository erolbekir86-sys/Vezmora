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

SMTP = ["SMTP_HOST", "SMTP_FROM"]
GOOGLE_OAUTH = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]
META_OAUTH = ["META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"]

# These flags must remain false during the private beta. The preflight treats an
# accidental enablement as a safety failure rather than merely informational.
BETA_LOCKED_FLAGS = [
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
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


def build_report() -> dict[str, Any]:
    core_missing = _missing(CORE_REQUIRED)
    if not database_configured():
        core_missing.append("DATABASE_URL/POSTGRES_URL (or legacy TURSO_DATABASE_URL + TURSO_AUTH_TOKEN)")

    billing_missing = _missing(BILLING)
    smtp_missing = _missing(SMTP)
    google_oauth_missing = _missing(GOOGLE_OAUTH)
    meta_oauth_missing = _missing(META_OAUTH)
    unsafe_flags = [name for name in BETA_LOCKED_FLAGS if enabled(name)]

    return {
        "brand": "Vexmera",
        "phase": "private_beta",
        "core_ready": not core_missing,
        "database_ready": database_configured(),
        "billing_ready": not billing_missing,
        "smtp_ready": not smtp_missing,
        "google_oauth_ready": not google_oauth_missing,
        "google_ads_developer_token_ready": configured("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "meta_oauth_ready": not meta_oauth_missing,
        "serverless_enabled": enabled("VEZMORA_SERVERLESS"),
        "beta_execution_locked": not unsafe_flags,
        "missing": {
            "core": core_missing,
            "billing": billing_missing,
            "smtp": smtp_missing,
            "google_oauth": google_oauth_missing,
            "meta_oauth": meta_oauth_missing,
        },
        "unsafe_beta_flags": unsafe_flags,
    }


def _status(value: bool) -> str:
    return "READY" if value else "MISSING CONFIG"


def print_report(report: dict[str, Any]) -> None:
    print("Vexmera deployment preflight")
    print(f"phase: {report['phase']}")
    print(f"core: {_status(bool(report['core_ready']))}")
    print(f"database: {_status(bool(report['database_ready']))}")
    print(f"billing: {_status(bool(report['billing_ready']))}")
    print(f"transactional email: {_status(bool(report['smtp_ready']))}")
    print(f"Google OAuth: {_status(bool(report['google_oauth_ready']))}")
    print(f"Google Ads developer token: {_status(bool(report['google_ads_developer_token_ready']))}")
    print(f"Meta OAuth: {_status(bool(report['meta_oauth_ready']))}")
    print(f"serverless mode enabled: {bool(report['serverless_enabled'])}")
    print(f"private-beta execution locks: {'SAFE' if report['beta_execution_locked'] else 'UNSAFE'}")

    missing = report["missing"]
    for group in ("core", "billing", "smtp", "google_oauth", "meta_oauth"):
        values = missing[group]
        print(f"Missing {group} variables:", ", ".join(values) if values else "none")
    print(
        "Unsafe beta flags:",
        ", ".join(report["unsafe_beta_flags"]) if report["unsafe_beta_flags"] else "none",
    )
    print("Secret values are intentionally never printed.")


def main() -> int:
    report = build_report()
    if "--json" in sys.argv[1:]:
        # The report contains names and booleans only. It never contains values
        # from environment variables, making it safe to archive in CI logs.
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)
    return 1 if (not report["core_ready"] or not report["beta_execution_locked"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
