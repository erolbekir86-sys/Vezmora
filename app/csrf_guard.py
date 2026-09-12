from __future__ import annotations

from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import SESSION_COOKIE

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_CROSS_ORIGIN_FETCH_SITES = frozenset({"cross-site", "same-site"})
_PUBLIC_BROWSER_AUTH_PATHS = frozenset(
    {
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/password-reset/request",
        "/api/auth/password-reset/confirm",
    }
)


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


def _origin_guard_required(request: Request) -> bool:
    if request.method.upper() not in _UNSAFE_METHODS or not _is_api_path(request.url.path):
        return False
    if request.cookies.get(SESSION_COOKIE):
        return True
    return request.url.path.rstrip("/") in _PUBLIC_BROWSER_AUTH_PATHS


def install_csrf_guard(app: FastAPI) -> None:
    """Reject cross-origin browser mutations at session and auth boundaries.

    SameSite=Lax protects cookie delivery but does not cover login-CSRF against an
    unauthenticated browser, and sibling origins are same-site. Public login,
    registration and password-reset POSTs therefore get the same Origin / Fetch
    Metadata check as authenticated API mutations. API clients without browser
    Origin/Fetch Metadata remain compatible; Stripe webhooks and cron are outside
    this narrow public-auth allowlist.
    """

    if getattr(app.state, "vexmera_csrf_guard_installed", False):
        return

    @app.middleware("http")
    async def mutation_origin_guard(request: Request, call_next):
        if _origin_guard_required(request):
            authenticated = bool(request.cookies.get(SESSION_COOKIE))
            detail = (
                "Cross-origin authenticated request blocked"
                if authenticated
                else "Cross-origin authentication request blocked"
            )

            fetch_site = (request.headers.get("sec-fetch-site") or "").strip().lower()
            if fetch_site in _CROSS_ORIGIN_FETCH_SITES:
                return JSONResponse(status_code=403, content={"detail": detail})

            origin_header = (request.headers.get("origin") or "").strip()
            if origin_header:
                origin = _origin_tuple(origin_header)
                if origin is None or origin != _request_origin(request):
                    return JSONResponse(status_code=403, content={"detail": detail})

        return await call_next(request)

    app.state.vexmera_csrf_guard_installed = True
