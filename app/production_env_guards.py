from __future__ import annotations

import os


_PRIVATE_BETA_DISABLED_FLAGS = (
    "VEZMORA_DEV_SHOW_TOKENS",
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
)

_CURRENT_PRICING_VERSION = "2026-09-start-growth-pro"
_CURRENT_PRICE_ENV = {
    "STRIPE_PRICE_STARTER": "STRIPE_PRICE_START",
    "STRIPE_PRICE_GROWTH": "STRIPE_PRICE_GROWTH",
    "STRIPE_PRICE_SCALE": "STRIPE_PRICE_PRO",
}
_LEGACY_ONLY_PRICE_ENV = ("STRIPE_PRICE_STARTER", "STRIPE_PRICE_SCALE")


def _current_pricing_verified() -> bool:
    return (
        (os.getenv("VEZMORA_STRIPE_PRICING_VERSION") or "").strip() == _CURRENT_PRICING_VERSION
        and all((os.getenv(name) or "").strip() for name in ("STRIPE_PRICE_START", "STRIPE_PRICE_GROWTH", "STRIPE_PRICE_PRO"))
    )


def apply_production_env_guards() -> None:
    """Fail closed for unsafe Private Beta-only overrides on Vercel.

    Local development can still opt into explicit test behavior. On Vercel,
    however, stale or accidental environment overrides must not expose reset or
    invite tokens, unlock external ad mutations, enable autonomous execution,
    request Meta's ads_management scope, allow insecure absolute links in email,
    or make the historical Stripe pricing configuration appear current.
    """
    if not os.getenv("VERCEL"):
        return

    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        os.environ[name] = "false"

    # Password-reset and invite emails build absolute URLs from VEZMORA_APP_URL.
    # Never allow an accidental http:// production value to put bearer-style
    # tokens onto an insecure transport. Removing the value makes the existing
    # readiness/preflight checks fail closed instead of silently using it.
    app_url = (os.getenv("VEZMORA_APP_URL") or "").strip()
    if app_url and not app_url.lower().startswith("https://"):
        os.environ.pop("VEZMORA_APP_URL", None)

    # The legacy Vercel entrypoint still has a boolean-only Stripe configuration
    # check using STARTER/GROWTH/SCALE variable names. Prevent stale historical
    # STARTER/SCALE values from making that diagnostic green. Growth keeps the
    # same variable name in both models, so it is never cleared. Compatibility
    # aliases are exposed only when the exact current pricing version is verified.
    if _current_pricing_verified():
        for legacy_name, current_name in _CURRENT_PRICE_ENV.items():
            os.environ[legacy_name] = (os.getenv(current_name) or "").strip()
    else:
        for legacy_name in _LEGACY_ONLY_PRICE_ENV:
            os.environ.pop(legacy_name, None)
