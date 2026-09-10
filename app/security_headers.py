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
_OAUTH_CALLBACK_PATHS = frozenset(
    {
        "/api/connectors/google/callback",
        "/api/connectors/google/callback/",
        "/api/connectors/meta/callback",
        "/api/connectors/meta/callback/",
    }
)
_INSTALL_STATE_ATTR = "_vexmera_security_headers_installed"


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
    query_keys = request.query_params.keys()
    sensitive_oauth_callback = request.url.path in _OAUTH_CALLBACK_PATHS and (
        "code" in query_keys or "state" in query_keys
    )
    if (
        request.url.path in _PRODUCT_PATHS
        or _SENSITIVE_CAPABILITY_QUERY_KEYS.intersection(query_keys)
        or sensitive_oauth_callback
    ):
        response.headers["Referrer-Policy"] = "no-referrer"


def install_security_headers(app: FastAPI) -> None:
    """Add browser hardening headers without changing application routing or CSP.

    The installer is intentionally idempotent because both the package bootstrap
    and the deployment entrypoint may install the canonical policy depending on
    import order. A single app instance must never accumulate duplicate security
    middleware layers.
    """
    if getattr(app.state, _INSTALL_STATE_ATTR, False):
        return
    setattr(app.state, _INSTALL_STATE_ATTR, True)

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
