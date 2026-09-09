from __future__ import annotations

import os
from typing import Any

CURRENT_PRICING_VERSION = "2026-09-start-growth-pro"

# Canonical customer-facing plan names. Legacy stored/API values are accepted
# through PLAN_ALIASES so existing beta workspaces keep working without a risky
# data migration.
PLAN_ALIASES = {
    "start": "start",
    "starter": "start",
    "growth": "growth",
    "pro": "pro",
    "scale": "pro",
}

PLANS: dict[str, dict[str, Any]] = {
    "start": {
        "label": "Start",
        "monthly_price_sek": 995,
        "ai_runs": 100,
        "jobs": 300,
        "team_members": 1,
        "campaign_rows": 10_000,
        "positioning": "For solo operators and small local businesses",
    },
    "growth": {
        "label": "Growth",
        "monthly_price_sek": 1_495,
        "ai_runs": 1_000,
        "jobs": 5_000,
        "team_members": 3,
        "campaign_rows": 250_000,
        "positioning": "For growing teams running multiple marketing channels",
    },
    "pro": {
        "label": "Pro",
        "monthly_price_sek": 2_995,
        "ai_runs": 10_000,
        "jobs": 50_000,
        "team_members": 10,
        "campaign_rows": 2_000_000,
        "positioning": "For larger teams, agencies and higher-volume operations",
    },
}

STRIPE_PRICE_ENV = {
    "start": "STRIPE_PRICE_START",
    "growth": "STRIPE_PRICE_GROWTH",
    "pro": "STRIPE_PRICE_PRO",
}

EXPECTED_MONTHLY_SEK_ORE = {
    "start": 99_500,
    "growth": 149_500,
    "pro": 299_500,
}


def normalize_plan(plan: str) -> str:
    normalized = PLAN_ALIASES.get(str(plan or "").strip().lower())
    if not normalized:
        raise ValueError(f"Unknown Vexmera plan: {plan}")
    return normalized


def checkout_pricing_reconciled() -> bool:
    """Return true only after the current Stripe sandbox model is explicitly approved.

    Merely having Stripe keys or legacy price IDs configured must never open new
    Checkout sessions. The operator must set the exact pricing-version marker
    after the Start/Growth/Pro sandbox catalog has been verified.
    """
    return (os.getenv("VEZMORA_STRIPE_PRICING_VERSION") or "").strip() == CURRENT_PRICING_VERSION


def current_stripe_prices_configured() -> bool:
    return all((os.getenv(name) or "").strip() for name in STRIPE_PRICE_ENV.values())
