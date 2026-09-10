from __future__ import annotations

import hmac
import os

from fastapi import HTTPException


def require_cron_constant_time(authorization: str | None) -> None:
    """Validate the internal cron bearer secret without data-dependent string comparison."""
    secret = (os.getenv("CRON_SECRET") or "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not configured")

    provided = authorization or ""
    expected = f"Bearer {secret}"
    if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Unauthorized cron request")


def install_cron_auth_safety() -> None:
    """Replace app.main's cron authorization helper after its routes are loaded."""
    from . import main as main_module

    main_module._require_cron = require_cron_constant_time
