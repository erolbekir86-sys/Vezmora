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
_BASELINE_CSP = "base-uri 'self'; object-src 'none'; form-action 'self'; frame-ancestors 'none'"
_SENSITIVE_CAPABILITY_QUERY_KEYS = frozenset({"reset", "invite", "session_id"})
_PRODUCT_PATHS = frozenset({"/app", "/app/"})
_OAUTH_CALLBACK_PATHS = frozenset(
    {
        "/api/connectors/google/callback",
        "/api/connectors/google/callback/",
        "/api/connectors/meta/callback",
        "/api/connectors/meta/callback/",
    }
)


def _https_runtime() -> bool:
    if (os.getenv("VERCEL") or "").strip():
        return True
    return (os.getenv("VEZMORA_APP_URL") or "").strip().lower().startswith("https://")


def _query_keys(request: Request) -> frozenset[str]:
    """Normalize query parameter names before applying capability safeguards."""
    return frozenset(key.casefold() for key in request.query_params.keys())


def _is_private_or_capability_surface(request: Request) -> bool:
    path = request.url.path
    return (
        path == "/api"
        or path.startswith("/api/")
        or path == "/health"
        or path.startswith("/health/")
        or path in _PRODUCT_PATHS
        or bool(_SENSITIVE_CAPABILITY_QUERY_KEYS.intersection(_query_keys(request)))
    )


def _protect_private_cache(request: Request, response) -> None:
    if not _is_private_or_capability_surface(request):
        return
    for name, value in _API_NO_STORE_HEADERS.items():
        response.headers.setdefault(name, value)


def _protect_private_indexing(request: Request, response) -> None:
    """Keep private, diagnostic and one-time capability URLs out of search indexes."""
    if _is_private_or_capability_surface(request):
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive")


def _protect_capability_referrer(request: Request, response) -> None:
    """Keep private app URLs and one-time capability parameters out of Referer headers."""
    query_keys = _query_keys(request)
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
    """Add low-risk browser hardening headers at the application boundary."""
    if getattr(app.state, "vexmera_security_headers_installed", False):
        return

    @app.middleware("http")
    async def _security_headers(request: Request, call_next):
        response = await call_next(request)
        _protect_private_cache(request, response)
        _protect_private_indexing(request, response)
        _protect_capability_referrer(request, response)
        response.headers.setdefault("Content-Security-Policy", _BASELINE_CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        # Prevent speculative DNS lookups from leaking third-party hostnames before
        # the user actually navigates or a resource is intentionally requested.
        response.headers.setdefault("X-DNS-Prefetch-Control", "off")
        # Isolate Vexmera's browsing context from unrelated cross-origin windows
        # while preserving OAuth/payment popup compatibility.
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
        # Ask supporting browsers to isolate this origin into its own agent cluster.
        # setdefault keeps route-specific compatibility overrides possible.
        response.headers.setdefault("Origin-Agent-Cluster", "?1")
        if _https_runtime():
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    app.state.vexmera_security_headers_installed = True
