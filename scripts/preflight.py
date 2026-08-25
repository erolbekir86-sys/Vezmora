from __future__ import annotations

import os
import sys

REQUIRED = [
    "VEZMORA_APP_URL",
    "VEZMORA_SECRET_KEY",
    "OPENAI_API_KEY",
    "TURSO_DATABASE_URL",
    "TURSO_AUTH_TOKEN",
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


def main() -> int:
    missing = [name for name in REQUIRED if not configured(name)]
    billing_missing = [name for name in BILLING if not configured(name)]
    print("Vezmora deployment preflight")
    print(f"core: {'READY' if not missing else 'MISSING CONFIG'}")
    print(f"billing: {'READY' if not billing_missing else 'MISSING CONFIG'}")
    print(f"serverless mode: {os.getenv('VEZMORA_SERVERLESS', 'false')}")
    print("Missing core variables:", ", ".join(missing) if missing else "none")
    print("Missing billing variables:", ", ".join(billing_missing) if billing_missing else "none")
    print("Secret values are intentionally never printed.")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
