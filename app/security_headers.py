from __future__ import annotations

import os

from fastapi import FastAPI, Request

_API_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "CDN-Cache-Control": "no-store",
    "Vercel-CDN-Cache-Control": "no-store",
}
_SENSITIVE_CAPABILITY_QUERY_KEYS = frozenset({"reset", "invite"})
_PRODUCT_PATHS = frozenset({"/app", "/app/"})


def _https_runtime() -> bool:
    if (os.getenv("VERCEL") or "").strip():
        return True
    return (os.getenv("VEZMORA_APP_URL") or "").strip().lower().startswith("https://")


def _protect_private_cache(request: Request, response) -> None:
    path = request.url.path
    protected = (
        path == "/api"
        or path.startswith("/api/")
        or path == "/health"
        or path.startswith("/health/")
    )
    if not protected:
        return
    for name, value in _API_NO_STORE_HEADERS.items():
        response.headers.setdefault(name, value)


def _protect_capability_referrer(request: Request, response) -> None:
    """Keep private app URLs and one-time capability parameters out of Referer headers."""
    if request.url.path in _PRODUCT_PATHS or _SENSITIVE_CAPABILITY_QUERY_KEYS.intersection(request.query_params.keys()):
        response.headers["Referrer-Policy"] = "no-referrer"


def install_security_headers(app: FastAPI) -> None:
    """Add browser hardening headers without changing application routing or CSP."""

    @app.middleware("http")
    async def _security_headers(request: Request, call_next):
        response = await call_next(request)
        _protect_private_cache(request, response)
        _protect_capability_referrer(request, response)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        if _https_runtime():
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
