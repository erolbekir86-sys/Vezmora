from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


_PUBLIC_HEALTH = {
    "ok": True,
    "service": "vexmera",
    "version": "0.6.1",
}


def install_public_health_guard(app: FastAPI) -> None:
    """Keep production liveness useful without exposing runtime configuration.

    The detailed /health payload remains available outside Vercel for local QA.
    On Vercel, public callers only need a stable liveness response and should
    not learn which secrets, billing providers, storage backends or workers are
    configured.
    """

    if getattr(app.state, "vexmera_public_health_guard_installed", False):
        return

    @app.middleware("http")
    async def minimal_public_health(request: Request, call_next):
        if os.getenv("VERCEL") and request.method == "GET" and request.url.path == "/health":
            return JSONResponse(_PUBLIC_HEALTH)
        return await call_next(request)

    app.state.vexmera_public_health_guard_installed = True
