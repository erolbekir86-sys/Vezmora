from __future__ import annotations

import os


_PRIVATE_BETA_DISABLED_FLAGS = (
    "VEZMORA_DEV_SHOW_TOKENS",
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
)


def apply_production_env_guards() -> None:
    """Fail closed for unsafe Private Beta-only overrides on Vercel.

    Local development can still opt into explicit test behavior. On Vercel,
    however, stale or accidental environment overrides must not expose reset or
    invite tokens, unlock external ad mutations, enable autonomous execution,
    or request Meta's ads_management scope during the Private Beta.
    """
    if os.getenv("VERCEL"):
        for name in _PRIVATE_BETA_DISABLED_FLAGS:
            os.environ[name] = "false"
