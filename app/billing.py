from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from .pricing import PLANS, checkout_pricing_reconciled, current_stripe_prices_configured, normalize_plan
from .store import get_workspace_settings, usage_summary


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


def _stored_plan(value: object) -> str:
    # Existing beta databases can still contain the historical values
    # "starter" and "scale". Treat them as aliases instead of requiring a
    # production data migration just to adopt the current public plan names.
    try:
        return normalize_plan(str(value or "start"))
    except ValueError:
        return "start"


def billing_status(workspace_id: int) -> dict[str, Any]:
    settings = get_workspace_settings(workspace_id)
    plan = _stored_plan(settings.get("plan"))
    usage = usage_summary(workspace_id)
    limits = PLANS[plan]
    stripe_ready = bool(
        checkout_pricing_reconciled()
        and current_stripe_prices_configured()
        and os.getenv("STRIPE_SECRET_KEY")
        and os.getenv("STRIPE_WEBHOOK_SECRET")
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
