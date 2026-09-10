from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .agent import MODEL
from .auth import SESSION_COOKIE, require_user
from .scheduler import scheduler_enabled


_PUBLIC_HEALTH = {
    "ok": True,
    "service": "vexmera",
    "version": "0.6.1",
}
_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "CDN-Cache-Control": "no-store",
    "Vercel-CDN-Cache-Control": "no-store",
}


def _public_runtime_payload() -> dict[str, object]:
    """Return only deployment identity needed by public production preflight."""
    return {
        **_PUBLIC_HEALTH,
        "platform": "vercel",
        "environment": (os.getenv("VERCEL_ENV") or "").strip() or None,
        "deployment_revision": (os.getenv("VERCEL_GIT_COMMIT_SHA") or "").strip() or None,
    }


def _authenticated_product_health() -> dict[str, object]:
    """Return only the runtime status fields consumed by the signed-in product UI."""
    return {
        **_PUBLIC_HEALTH,
        "model": MODEL,
        "api_key_configured": bool((os.getenv("OPENAI_API_KEY") or "").strip()),
        "scheduler_enabled": scheduler_enabled(),
    }


def _has_valid_session(request: Request) -> bool:
    """Validate the session before disclosing authenticated-only status booleans."""
    raw_session = request.cookies.get(SESSION_COOKIE)
    if not raw_session:
        return False
    try:
        require_user(raw_session)
    except Exception:
        # Health must fail closed to the anonymous payload if auth/storage is unavailable.
        return False
    return True


def install_public_health_guard(app: FastAPI) -> None:
    """Keep production liveness useful without exposing runtime configuration.

    Detailed health/runtime payloads remain available outside Vercel for local
    operator QA. On Vercel, anonymous callers only receive stable liveness plus a
    minimal deployment identity. A validated product session may receive the very
    small set of non-secret booleans already consumed by the signed-in UI, while
    storage, OAuth, billing, SMTP and secret inventory details remain hidden.
    """

    if getattr(app.state, "vexmera_public_health_guard_installed", False):
        return

    @app.middleware("http")
    async def minimal_public_health(request: Request, call_next):
        if os.getenv("VERCEL") and request.method == "GET":
            if request.url.path == "/health":
                payload = _authenticated_product_health() if _has_valid_session(request) else _PUBLIC_HEALTH
                return JSONResponse(payload, headers=_NO_STORE_HEADERS)
            if request.url.path == "/health/runtime":
                return JSONResponse(_public_runtime_payload(), headers=_NO_STORE_HEADERS)
        return await call_next(request)

    app.state.vexmera_public_health_guard_installed = True
