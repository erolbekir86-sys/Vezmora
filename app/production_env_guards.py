from __future__ import annotations

import os


_PRIVATE_BETA_DISABLED_FLAGS = (
    "VEZMORA_DEV_SHOW_TOKENS",
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
)
_LEGACY_ONLY_PRICE_ENV = ("STRIPE_PRICE_STARTER", "STRIPE_PRICE_SCALE")


def apply_production_env_guards() -> None:
    """Fail closed for unsafe Private Beta-only overrides on Vercel.

    Local development can still opt into explicit test behavior. On Vercel,
    however, stale or accidental environment overrides must not expose reset or
    invite tokens, unlock external ad mutations, enable autonomous execution,
    request Meta's ads_management scope, allow insecure absolute links in email,
    or revive historical Stripe price variable names.
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

    # Current billing uses only STRIPE_PRICE_START/GROWTH/PRO. Historical
    # STARTER/SCALE aliases must not be synthesized in production because they
    # can make stale diagnostics or future code paths mistake old catalog state
    # for the verified Start/Growth/Pro model. Growth already keeps its canonical
    # variable name and current price variables are intentionally left untouched.
    for legacy_name in _LEGACY_ONLY_PRICE_ENV:
        os.environ.pop(legacy_name, None)
