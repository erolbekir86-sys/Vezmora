from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


_PRODUCTION_DOC_PATHS = frozenset({
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
})

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Robots-Tag": "noindex, nofollow",
}


def install_production_docs_guard(app: FastAPI) -> None:
    """Keep FastAPI's developer schema/docs available locally but not on Vercel.

    The routes remain part of the application for local development and direct
    Python introspection. Public HTTP access is hidden for every method in Vercel
    deployments so method probing cannot distinguish these internal framework
    routes from an ordinary missing path.
    """
    if getattr(app.state, "vexmera_production_docs_guard_installed", False):
        return

    @app.middleware("http")
    async def hide_framework_docs_in_vercel(request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if os.getenv("VERCEL") and path in _PRODUCTION_DOC_PATHS:
            return JSONResponse(
                status_code=404,
                content={"detail": "Not Found"},
                headers=_NO_STORE_HEADERS,
            )
        return await call_next(request)

    app.state.vexmera_production_docs_guard_installed = True
