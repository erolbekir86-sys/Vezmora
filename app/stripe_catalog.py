from __future__ import annotations

import os
from typing import Any, Mapping

from .pricing import (
    CURRENT_PRICING_VERSION,
    EXPECTED_MONTHLY_SEK_ORE,
    STRIPE_PRICE_ENV,
    normalize_plan,
)


def _field(value: object, name: str, default: object = None) -> object:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _int_value(value: object, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _stripe_client(secret: str):
    try:
        from stripe import StripeClient
    except ImportError as exc:
        raise RuntimeError("stripe_sdk_unavailable") from exc
    return StripeClient(secret, max_network_retries=2)


def price_validation_checks(plan: str, payload: object, configured_price_id: str | None = None) -> dict[str, bool]:
    """Return non-secret checks for one current Vexmera Stripe sandbox Price."""
    try:
        canonical = normalize_plan(plan)
    except ValueError:
        return {"known_plan": False}

    recurring = _field(payload, "recurring", {})
    checks = {
        "known_plan": True,
        "price_object": str(_field(payload, "object", "")).lower() == "price",
        "active": _field(payload, "active") is True,
        "sandbox": _field(payload, "livemode") is False,
        "currency_sek": str(_field(payload, "currency", "")).lower() == "sek",
        "recurring_type": str(_field(payload, "type", "")).lower() == "recurring",
        "monthly_interval": str(_field(recurring, "interval", "")).lower() == "month",
        "interval_count_one": _int_value(_field(recurring, "interval_count", 0), 0) == 1,
        "expected_amount": _int_value(_field(payload, "unit_amount", -1)) == EXPECTED_MONTHLY_SEK_ORE[canonical],
    }
    if configured_price_id is not None:
        checks["id_matches_configuration"] = str(_field(payload, "id", "")) == configured_price_id
    return checks


def validate_price_payload(plan: str, payload: object, configured_price_id: str | None = None) -> tuple[bool, str]:
    """Validate one Price while preserving the historical `(ok, reason)` API."""
    checks = price_validation_checks(plan, payload, configured_price_id)
    reason_map = {
        "known_plan": "unknown_plan",
        "price_object": "not_a_price",
        "active": "inactive",
        "sandbox": "livemode_not_sandbox",
        "currency_sek": "currency_mismatch",
        "recurring_type": "not_recurring",
        "monthly_interval": "interval_mismatch",
        "interval_count_one": "interval_mismatch",
        "expected_amount": "amount_mismatch",
        "id_matches_configuration": "price_id_mismatch",
    }
    for check, passed in checks.items():
        if not passed:
            return False, reason_map[check]
    return True, "ok"


def verify_configured_prices(client: Any | None = None) -> dict[str, Any]:
    """Verify the configured current-model Stripe sandbox catalog read-only.

    This is the canonical Vexmera Stripe catalog preflight. It retrieves only the
    three configured Price objects and returns safe booleans/reason codes. Secret
    keys, Price IDs, Product IDs, raw Stripe payloads and raw Stripe exceptions are
    deliberately excluded from the result.

    `catalog_ok` proves the configured Start/Growth/Pro Prices are active test-mode
    SEK monthly recurring Prices at exactly 995/1495/2995 SEK. Final `ok` also
    requires the explicit current pricing-version approval marker, which remains a
    separate operator-controlled gate before Checkout can open.
    """
    secret = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    marker_matches = (os.getenv("VEZMORA_STRIPE_PRICING_VERSION") or "").strip() == CURRENT_PRICING_VERSION
    price_ids = {plan: (os.getenv(env) or "").strip() for plan, env in STRIPE_PRICE_ENV.items()}
    configured = bool(secret) and all(price_ids.values())
    blockers: list[str] = []

    if not secret:
        blockers.append("stripe_secret_key_missing")
    for plan, price_id in price_ids.items():
        if not price_id:
            blockers.append(f"{plan}_price_id_missing")

    result: dict[str, Any] = {
        "configured": configured,
        "ok": False,
        "catalog_ok": False,
        "pricing_version_marker_matches": marker_matches,
        "expected_pricing_version": CURRENT_PRICING_VERSION,
        "stripe_secret_configured": bool(secret),
        "scope": "stripe_sandbox_catalog_read_only",
        "plans": {},
        "blockers": blockers,
    }

    active_client = client
    if active_client is None and configured:
        try:
            active_client = _stripe_client(secret)
        except RuntimeError as exc:
            blockers.append(str(exc))

    for plan, price_id in price_ids.items():
        if not price_id:
            result["plans"][plan] = {
                "configured": False,
                "retrieved": False,
                "ok": False,
                "reason": "not_configured",
                "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
            }
            continue

        if active_client is None:
            result["plans"][plan] = {
                "configured": True,
                "retrieved": False,
                "ok": False,
                "reason": "client_unavailable",
                "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
            }
            continue

        try:
            payload = active_client.v1.prices.retrieve(price_id)
        except Exception:
            plan_result = {
                "configured": True,
                "retrieved": False,
                "ok": False,
                "reason": "lookup_failed",
                "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
            }
            blockers.append(f"{plan}_price_lookup_failed")
        else:
            checks = price_validation_checks(plan, payload, price_id)
            ok, reason = validate_price_payload(plan, payload, price_id)
            plan_result = {
                "configured": True,
                "retrieved": True,
                "ok": ok,
                "reason": reason,
                "checks": checks,
                "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
            }
            blockers.extend(f"{plan}_{check}" for check, passed in checks.items() if not passed)
        result["plans"][plan] = plan_result

    catalog_ok = configured and all(bool(result["plans"].get(plan, {}).get("ok")) for plan in STRIPE_PRICE_ENV)
    if catalog_ok and not marker_matches:
        blockers.append("pricing_version_marker_not_approved")

    result["catalog_ok"] = catalog_ok
    result["ok"] = catalog_ok and marker_matches
    result["note"] = (
        "Read-only Stripe sandbox catalog verification. No products, prices, Checkout sessions, "
        "subscriptions, customers, webhooks, environment variables or live-mode state are changed."
    )
    return result
