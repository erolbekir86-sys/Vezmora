from __future__ import annotations

import os


def apply_production_env_guards() -> None:
    """Fail closed for development-only response behavior on Vercel.

    VEZMORA_DEV_SHOW_TOKENS exists only to make local development and tests
    convenient. A stale Vercel environment override must never cause password
    reset or invite tokens to be returned in HTTP responses.
    """
    if os.getenv("VERCEL"):
        os.environ["VEZMORA_DEV_SHOW_TOKENS"] = "false"
