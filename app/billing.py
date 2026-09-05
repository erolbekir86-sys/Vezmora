from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from .store import get_workspace_settings, usage_summary

# Customer-facing plan limits are kept in one place so the app, pricing copy,
# and backend enforcement can stay aligned. Prices are displayed in the UI;
# Stripe Price IDs remain configured through environment variables.
PLANS: dict[str, dict[str, Any]] = {
    "starter": {
        "label": "Starter",
        "monthly_price_sek": 1_499,
        "ai_runs": 100,
        "jobs": 300,
        "team_members": 1,
        "campaign_rows": 10_000,
        "positioning": "For solo operators and small local businesses",
    },
    "growth": {
        "label": "Growth",
        "monthly_price_sek": 2_999,
        "ai_runs": 1_000,
        "jobs": 5_000,
        "team_members": 3,
        "campaign_rows": 250_000,
        "positioning": "For growing teams running multiple marketing channels",
    },
    "scale": {
        "label": "Scale",
        "monthly_price_sek": 5_999,
        "ai_runs": 10_000,
        "jobs": 50_000,
        "team_members": 10,
        "campaign_rows": 2_000_000,
        "positioning": "For larger teams, agencies and higher-volume operations",
    },
}


def _trial_active(settings: dict[str, Any]) -> bool:
    end = settings.get("trial_ends_at")
    if not end:
        return settings.get("billing_status") == "trialing"
    try:
        dt = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < dt.astimezone(timezone.utc)
    except ValueError:
        return False


def billing_status(workspace_id: int) -> dict[str, Any]:
    settings = get_workspace_settings(workspace_id)
    plan = settings.get("plan") or "starter"
    usage = usage_summary(workspace_id)
    limits = PLANS.get(plan, PLANS["starter"])
    stripe_ready = bool(
        os.getenv("STRIPE_SECRET_KEY")
        and os.getenv("STRIPE_PRICE_STARTER")
        and os.getenv("STRIPE_PRICE_GROWTH")
        and os.getenv("STRIPE_PRICE_SCALE")
    )
    return {
        "plan": plan,
        "limits": limits,
        "usage": usage,
        "billing_status": settings.get("billing_status") or "trialing",
        "trial_ends_at": settings.get("trial_ends_at"),
        "trial_active": _trial_active(settings),
        "stripe_customer_attached": bool(settings.get("stripe_customer_id")),
        "subscription_attached": bool(settings.get("stripe_subscription_id")),
        "checkout_ready": stripe_ready,
    }


def enforce_limit(workspace_id: int, kind: str) -> None:
    status = billing_status(workspace_id)
    billing_state = str(status.get("billing_status") or "trialing")
    if billing_state in {"canceled", "unpaid", "incomplete_expired"} and not status.get("trial_active"):
        raise HTTPException(status_code=402, detail="An active Vexmera subscription is required")
    limit = status["limits"].get(kind)
    used = status["usage"].get(kind, 0)
    if limit is not None and used >= limit:
        raise HTTPException(status_code=402, detail=f"{status['plan']} plan limit reached for {kind}")
