from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse


_RAW_STATIC_ENTRYPOINTS = {
    "/static/index.html": "/app",
    "/static/landing.html": "/",
    "/static/privacy.html": "/privacy",
    "/static/terms.html": "/terms",
}

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


def install_static_entrypoint_guard(app: FastAPI) -> None:
    """Keep raw HTML source files from becoming alternate product entrypoints.

    Static JS/CSS/images remain untouched. Only known HTML entry documents are
    redirected to the server-owned canonical routes where the current security,
    onboarding, privacy, accessibility and beta UX layers are applied.
    """
    if getattr(app.state, "vexmera_static_entrypoint_guard_installed", False):
        return

    @app.middleware("http")
    async def canonicalize_raw_static_entrypoints(request: Request, call_next):
        target = _RAW_STATIC_ENTRYPOINTS.get(request.url.path)
        if target and request.method in {"GET", "HEAD"}:
            query = request.url.query
            location = f"{target}?{query}" if query else target
            return RedirectResponse(
                location,
                status_code=302,
                headers=_NO_STORE_HEADERS,
            )
        return await call_next(request)

    app.state.vexmera_static_entrypoint_guard_installed = True
