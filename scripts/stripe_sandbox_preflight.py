from __future__ import annotations

import json
import os
from typing import Any, Mapping

from app.pricing import (
    CURRENT_PRICING_VERSION,
    EXPECTED_MONTHLY_SEK_ORE,
    STRIPE_PRICE_ENV,
)


def _field(value: object, name: str, default: object = None) -> object:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _stripe_client_from_env():
    try:
        from stripe import StripeClient
    except ImportError as exc:
        raise RuntimeError("stripe_sdk_unavailable") from exc

    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        raise RuntimeError("stripe_secret_key_missing")
    return StripeClient(key, max_network_retries=2)


def _retrieve_price(client: Any, price_id: str) -> object:
    """Retrieve one Stripe Price. This helper performs a read only."""
    return client.v1.prices.retrieve(price_id)


def _inspect_price(plan: str, price: object, configured_price_id: str) -> dict[str, object]:
    recurring = _field(price, "recurring", {})
    checks = {
        "id_matches_configuration": str(_field(price, "id", "")) == configured_price_id,
        "active": _field(price, "active") is True,
        "sandbox": _field(price, "livemode") is False,
        "currency_sek": str(_field(price, "currency", "")).lower() == "sek",
        "recurring_type": str(_field(price, "type", "")).lower() == "recurring",
        "monthly_interval": str(_field(recurring, "interval", "")).lower() == "month",
        "interval_count_one": int(_field(recurring, "interval_count", 0) or 0) == 1,
        "expected_amount": int(_field(price, "unit_amount", -1) or -1) == EXPECTED_MONTHLY_SEK_ORE[plan],
    }
    return {
        "configured": True,
        "retrieved": True,
        "checks": checks,
        "ok": all(checks.values()),
        "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
    }


def build_stripe_sandbox_preflight(client: Any | None = None) -> dict[str, object]:
    """Verify the configured Vexmera Stripe sandbox catalog without mutating Stripe.

    The output deliberately excludes secret keys, raw Stripe errors and configured
    Price IDs. A successful catalog check is evidence that Start/Growth/Pro point
    at active SEK monthly sandbox prices with the exact current Vexmera amounts.
    Checkout remains closed until the explicit pricing-version marker also matches.
    """
    blockers: list[str] = []
    plans: dict[str, dict[str, object]] = {}

    marker_matches = (os.getenv("VEZMORA_STRIPE_PRICING_VERSION") or "").strip() == CURRENT_PRICING_VERSION
    secret_configured = bool((os.getenv("STRIPE_SECRET_KEY") or "").strip())
    if not secret_configured:
        blockers.append("stripe_secret_key_missing")

    configured_ids: dict[str, str] = {}
    for plan, env_name in STRIPE_PRICE_ENV.items():
        price_id = (os.getenv(env_name) or "").strip()
        configured_ids[plan] = price_id
        if not price_id:
            blockers.append(f"{plan}_price_id_missing")
            plans[plan] = {
                "configured": False,
                "retrieved": False,
                "ok": False,
                "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
            }

    active_client = client
    if active_client is None and secret_configured and all(configured_ids.values()):
        try:
            active_client = _stripe_client_from_env()
        except RuntimeError as exc:
            blockers.append(str(exc))

    if active_client is not None:
        for plan, price_id in configured_ids.items():
            if not price_id:
                continue
            try:
                price = _retrieve_price(active_client, price_id)
                result = _inspect_price(plan, price, price_id)
            except Exception:
                result = {
                    "configured": True,
                    "retrieved": False,
                    "ok": False,
                    "expected_monthly_sek_ore": EXPECTED_MONTHLY_SEK_ORE[plan],
                }
                blockers.append(f"{plan}_price_lookup_failed")
            else:
                failed_checks = [name for name, passed in result["checks"].items() if not passed]
                blockers.extend(f"{plan}_{name}" for name in failed_checks)
            plans[plan] = result

    catalog_ok = bool(plans) and all(bool(plans.get(plan, {}).get("ok")) for plan in STRIPE_PRICE_ENV)
    if catalog_ok and not marker_matches:
        blockers.append("pricing_version_marker_not_approved")

    return {
        "ok": catalog_ok and marker_matches,
        "scope": "stripe_sandbox_catalog_read_only",
        "catalog_ok": catalog_ok,
        "pricing_version_marker_matches": marker_matches,
        "expected_pricing_version": CURRENT_PRICING_VERSION,
        "stripe_secret_configured": secret_configured,
        "plans": plans,
        "blockers": blockers,
        "note": (
            "Read-only Stripe sandbox catalog verification. No products, prices, Checkout sessions, "
            "subscriptions, customers, webhooks, environment variables or live-mode state are changed. "
            "catalog_ok=true means the configured Start/Growth/Pro Price objects match the expected "
            "sandbox catalog; Checkout remains gated until pricing_version_marker_matches=true."
        ),
    }


def main() -> int:
    result = build_stripe_sandbox_preflight()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
