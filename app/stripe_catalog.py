from __future__ import annotations

import os
from typing import Any

import httpx

from .pricing import EXPECTED_MONTHLY_SEK_ORE, STRIPE_PRICE_ENV, normalize_plan


def validate_price_payload(plan: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate one current Vexmera Stripe Price without exposing identifiers."""
    try:
        canonical = normalize_plan(plan)
    except ValueError:
        return False, "unknown_plan"

    expected = EXPECTED_MONTHLY_SEK_ORE[canonical]
    if payload.get("object") != "price":
        return False, "not_a_price"
    if payload.get("active") is not True:
        return False, "inactive"
    if str(payload.get("currency") or "").lower() != "sek":
        return False, "currency_mismatch"
    if payload.get("unit_amount") != expected:
        return False, "amount_mismatch"
    recurring = payload.get("recurring") or {}
    if recurring.get("interval") != "month" or int(recurring.get("interval_count") or 1) != 1:
        return False, "interval_mismatch"
    return True, "ok"


def verify_configured_prices(timeout: float = 8.0) -> dict[str, Any]:
    """Verify configured current-model Stripe prices using safe reason codes only.

    The function never returns a Stripe secret, Price ID, Product ID, customer
    data, or raw Stripe payload. It is safe to use during controlled deployment
    verification after the Start/Growth/Pro sandbox catalog has been created.
    """
    secret = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    configured = bool(secret) and all((os.getenv(env) or "").strip() for env in STRIPE_PRICE_ENV.values())
    result: dict[str, Any] = {
        "configured": configured,
        "ok": False,
        "plans": {},
    }
    if not configured:
        for plan, env in STRIPE_PRICE_ENV.items():
            result["plans"][plan] = {
                "configured": bool((os.getenv(env) or "").strip()),
                "ok": False,
                "reason": "not_configured",
            }
        return result

    all_ok = True
    for plan, env in STRIPE_PRICE_ENV.items():
        price_id = (os.getenv(env) or "").strip()
        try:
            response = httpx.get(
                f"https://api.stripe.com/v1/prices/{price_id}",
                auth=(secret, ""),
                timeout=timeout,
            )
        except Exception:
            ok, reason = False, "network_error"
        else:
            if response.status_code != 200:
                ok, reason = False, f"stripe_http_{response.status_code}"
            else:
                try:
                    payload = response.json()
                except Exception:
                    ok, reason = False, "invalid_json"
                else:
                    ok, reason = validate_price_payload(plan, payload)
        result["plans"][plan] = {"configured": True, "ok": ok, "reason": reason}
        all_ok = all_ok and ok

    result["ok"] = all_ok
    return result
