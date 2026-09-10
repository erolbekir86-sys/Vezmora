from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from . import stripe_billing as _stripe

MAX_STRIPE_EVENT_ID_LENGTH = 255
MAX_STRIPE_EVENT_TYPE_LENGTH = 255


def _bounded_parse_webhook(payload: bytes, signature: str | None) -> dict[str, Any]:
    """Verify with Stripe first, then bound identifiers persisted in audit rows."""
    event = _bounded_parse_webhook._original(payload, signature)  # type: ignore[attr-defined]
    event_id = event.get("id")
    event_type = event.get("type")

    if not isinstance(event_id, str) or not event_id or len(event_id) > MAX_STRIPE_EVENT_ID_LENGTH:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook event id")
    if not isinstance(event_type, str) or not event_type or len(event_type) > MAX_STRIPE_EVENT_TYPE_LENGTH:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook event type")
    return event


def install_stripe_event_safety() -> None:
    if getattr(_stripe, "_vexmera_stripe_event_safety_installed", False):
        return
    _bounded_parse_webhook._original = _stripe.parse_webhook  # type: ignore[attr-defined]
    _stripe.parse_webhook = _bounded_parse_webhook
    _stripe._vexmera_stripe_event_safety_installed = True
