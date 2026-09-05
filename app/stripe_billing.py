from __future__ import annotations

import math
import os
import secrets
import string
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from .store import (
    get_workspace_settings,
    record_billing_event,
    set_workspace_billing,
    workspace_id_by_stripe_customer,
)

PRICE_ENV = {
    "starter": "STRIPE_PRICE_STARTER",
    "growth": "STRIPE_PRICE_GROWTH",
    "scale": "STRIPE_PRICE_SCALE",
}


def stripe_configured() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY"))


def _stripe_client():
    try:
        from stripe import StripeClient
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Stripe SDK is not installed. Run the project dependency install.") from exc
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY is not configured")
    return StripeClient(key, max_network_retries=2)


def _price_id(plan: str) -> str:
    env = PRICE_ENV.get(plan)
    price = os.getenv(env or "")
    if not price:
        raise HTTPException(status_code=503, detail=f"Stripe price is not configured for plan: {plan}")
    return price


def _integration_identifier() -> str:
    suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(8))
    return f"vezmora_beta_{suffix}"


def _trial_days(settings: dict[str, Any]) -> int:
    """Grant at most the unused part of the workspace's first beta trial.

    Registration currently starts the private-beta trial in Vexmera. Checkout
    must therefore never reset the clock to a fresh 14 days. If a local trial
    end exists, Stripe receives only the remaining whole-day ceiling so an
    immediate Checkout still receives the advertised trial while a late
    Checkout cannot extend it.
    """
    if settings.get("stripe_customer_id") or settings.get("stripe_subscription_id"):
        return 0

    configured_days = max(0, int(os.getenv("VEZMORA_TRIAL_DAYS", "14")))
    raw_end = settings.get("trial_ends_at")
    if not raw_end:
        return configured_days

    try:
        end = datetime.fromisoformat(str(raw_end).replace("Z", "+00:00"))
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        seconds = (end.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    except (TypeError, ValueError):
        return 0

    if seconds <= 0:
        return 0
    remaining_days = int(math.ceil(seconds / 86_400))
    return min(configured_days, remaining_days)


def create_checkout(workspace_id: int, email: str, plan: str) -> dict[str, Any]:
    client = _stripe_client()
    settings = get_workspace_settings(workspace_id)
    if settings.get("stripe_subscription_id") and str(settings.get("billing_status") or "") not in {"canceled", "incomplete_expired"}:
        raise HTTPException(status_code=409, detail="This workspace already has a Stripe subscription. Use the billing portal to manage it.")

    base_url = os.getenv("VEZMORA_APP_URL", "http://localhost:8000").rstrip("/")
    trial_days = _trial_days(settings)
    metadata = {
        "workspace_id": str(workspace_id),
        "plan": plan,
        "trial_days": str(trial_days),
    }
    subscription_data: dict[str, Any] = {"metadata": metadata}
    if trial_days:
        subscription_data["trial_period_days"] = trial_days

    params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": _price_id(plan), "quantity": 1}],
        "success_url": f"{base_url}/?billing=success&session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{base_url}/?billing=cancelled",
        "client_reference_id": str(workspace_id),
        "metadata": metadata,
        "subscription_data": subscription_data,
        "allow_promotion_codes": True,
        "integration_identifier": _integration_identifier(),
    }
    if settings.get("stripe_customer_id"):
        params["customer"] = settings["stripe_customer_id"]
    else:
        params["customer_email"] = email

    session = client.v1.checkout.sessions.create(params)
    return {"id": session.id, "url": session.url, "trial_days": trial_days}


def create_portal(workspace_id: int) -> dict[str, Any]:
    client = _stripe_client()
    settings = get_workspace_settings(workspace_id)
    customer = settings.get("stripe_customer_id")
    if not customer:
        raise HTTPException(status_code=409, detail="No Stripe customer is attached to this workspace")
    base_url = os.getenv("VEZMORA_APP_URL", "http://localhost:8000").rstrip("/")
    session = client.v1.billing_portal.sessions.create({"customer": customer, "return_url": f"{base_url}/?view=team"})
    return {"url": session.url}


def parse_webhook(payload: bytes, signature: str | None) -> dict[str, Any]:
    client = _stripe_client()
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET is not configured")
    if not signature:
        raise HTTPException(status_code=400, detail="Stripe-Signature header is required")
    try:
        event = client.construct_event(payload, signature, secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature") from exc
    return dict(event)


def _trial_end_iso(obj: dict[str, Any]) -> str | None:
    raw = obj.get("trial_end")
    if raw is None:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def apply_webhook(event: dict[str, Any]) -> dict[str, Any]:
    event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "")
    obj = ((event.get("data") or {}).get("object") or {})
    workspace_id: int | None = None
    metadata = obj.get("metadata") or {}
    if metadata.get("workspace_id"):
        try:
            workspace_id = int(metadata["workspace_id"])
        except (TypeError, ValueError):
            workspace_id = None
    customer = obj.get("customer")
    if workspace_id is None and customer:
        workspace_id = workspace_id_by_stripe_customer(str(customer))

    if event_id and not record_billing_event(workspace_id, event_id, event_type, event):
        return {"ok": True, "duplicate": True}

    if event_type == "checkout.session.completed" and workspace_id is not None:
        plan = str(metadata.get("plan") or "starter")
        trialing = int(metadata.get("trial_days") or 0) > 0
        set_workspace_billing(
            workspace_id,
            plan=plan,
            customer_id=str(obj.get("customer") or "") or None,
            subscription_id=str(obj.get("subscription") or "") or None,
            billing_status="trialing" if trialing else "active",
        )
    elif event_type in {"customer.subscription.updated", "customer.subscription.created"} and workspace_id is not None:
        plan = str(metadata.get("plan") or get_workspace_settings(workspace_id).get("plan") or "starter")
        set_workspace_billing(
            workspace_id,
            plan=plan,
            customer_id=str(customer or "") or None,
            subscription_id=str(obj.get("id") or "") or None,
            billing_status=str(obj.get("status") or "active"),
            trial_ends_at=_trial_end_iso(obj),
        )
    elif event_type == "customer.subscription.deleted" and workspace_id is not None:
        set_workspace_billing(workspace_id, billing_status="canceled", subscription_id=str(obj.get("id") or "") or None)
    elif event_type == "invoice.payment_failed" and workspace_id is not None:
        set_workspace_billing(workspace_id, billing_status="past_due")
    return {"ok": True, "workspace_id": workspace_id, "type": event_type}
