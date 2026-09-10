from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


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


def install_public_health_guard(app: FastAPI) -> None:
    """Keep production liveness useful without exposing runtime configuration.

    Detailed health/runtime payloads remain available outside Vercel for local
    operator QA. On Vercel, public callers only need stable liveness plus a
    minimal deployment identity. They should not learn which secrets, billing
    providers, storage backends, SMTP settings or OAuth providers are configured.
    """

    if getattr(app.state, "vexmera_public_health_guard_installed", False):
        return

    @app.middleware("http")
    async def minimal_public_health(request: Request, call_next):
        if os.getenv("VERCEL") and request.method == "GET":
            if request.url.path == "/health":
                return JSONResponse(_PUBLIC_HEALTH, headers=_NO_STORE_HEADERS)
            if request.url.path == "/health/runtime":
                return JSONResponse(_public_runtime_payload(), headers=_NO_STORE_HEADERS)
        return await call_next(request)

    app.state.vexmera_public_health_guard_installed = True
