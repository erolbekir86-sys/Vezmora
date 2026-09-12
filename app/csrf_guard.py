from __future__ import annotations

from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import SESSION_COOKIE

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_CROSS_ORIGIN_FETCH_SITES = frozenset({"cross-site", "same-site"})


def _origin_tuple(value: str) -> tuple[str, str] | None:
    """Normalize an HTTP(S) origin without accepting paths or opaque origins."""

    if not value or value == "null":
        return None
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    if parts.path not in {"", "/"} or parts.query or parts.fragment:
        return None
    return parts.scheme.lower(), parts.netloc.lower()


def _request_origin(request: Request) -> tuple[str, str]:
    return request.url.scheme.lower(), request.url.netloc.lower()


def _is_api_path(path: str) -> bool:
    return path == "/api" or path.startswith("/api/")


def install_csrf_guard(app: FastAPI) -> None:
    """Reject cross-origin browser mutations that carry a Vexmera session cookie.

    SameSite=Lax blocks cross-site cookie delivery, but it does not treat sibling
    subdomains as cross-site. This middleware adds a server-side defence-in-depth
    check using browser Origin / Fetch Metadata without imposing CSRF tokens on
    API clients, Stripe webhooks, cron jobs, or unauthenticated login/register
    requests.
    """

    if getattr(app.state, "vexmera_csrf_guard_installed", False):
        return

    @app.middleware("http")
    async def authenticated_mutation_origin_guard(request: Request, call_next):
        if (
            request.method.upper() in _UNSAFE_METHODS
            and _is_api_path(request.url.path)
            and request.cookies.get(SESSION_COOKIE)
        ):
            fetch_site = (request.headers.get("sec-fetch-site") or "").strip().lower()
            if fetch_site in _CROSS_ORIGIN_FETCH_SITES:
                return JSONResponse(status_code=403, content={"detail": "Cross-origin authenticated request blocked"})

            origin_header = (request.headers.get("origin") or "").strip()
            if origin_header:
                origin = _origin_tuple(origin_header)
                if origin is None or origin != _request_origin(request):
                    return JSONResponse(status_code=403, content={"detail": "Cross-origin authenticated request blocked"})

        return await call_next(request)

    app.state.vexmera_csrf_guard_installed = True
