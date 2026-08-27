from __future__ import annotations

import os

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


def configured(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def database_configured() -> bool:
    # Production prefers Neon/Postgres. Keep the legacy Turso pair supported
    # for compatibility with older deployments.
    if configured("DATABASE_URL") or configured("POSTGRES_URL"):
        return True
    return configured("TURSO_DATABASE_URL") and configured("TURSO_AUTH_TOKEN")


def main() -> int:
    missing = [name for name in CORE_REQUIRED if not configured(name)]
    if not database_configured():
        missing.append("DATABASE_URL/POSTGRES_URL (or legacy TURSO_DATABASE_URL + TURSO_AUTH_TOKEN)")

    billing_missing = [name for name in BILLING if not configured(name)]
    print("Vexmera deployment preflight")
    print(f"core: {'READY' if not missing else 'MISSING CONFIG'}")
    print(f"database: {'READY' if database_configured() else 'MISSING CONFIG'}")
    print(f"billing: {'READY' if not billing_missing else 'MISSING CONFIG'}")
    print(f"serverless mode: {os.getenv('VEZMORA_SERVERLESS', 'false')}")
    print("Missing core variables:", ", ".join(missing) if missing else "none")
    print("Missing billing variables:", ", ".join(billing_missing) if billing_missing else "none")
    print("Secret values are intentionally never printed.")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
