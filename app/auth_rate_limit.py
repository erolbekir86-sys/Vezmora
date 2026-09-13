from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class _Limit:
    max_requests: int
    window_seconds: int


# Conservative process-local abuse limits. These are defense in depth only;
# distributed/platform rate limiting remains the stronger production boundary.
_LIMITS: dict[str, _Limit] = {
    "/api/auth/login": _Limit(max_requests=30, window_seconds=300),
    "/api/auth/register": _Limit(max_requests=8, window_seconds=600),
    "/api/auth/password-reset/request": _Limit(max_requests=6, window_seconds=900),
    "/api/auth/password-reset/confirm": _Limit(max_requests=20, window_seconds=900),
}


def _rate_limit_enabled() -> bool:
    if os.getenv("VERCEL"):
        return True
    return os.getenv("VEZMORA_AUTH_RATE_LIMIT", "0").strip().lower() in {"1", "true", "yes", "on"}


class AuthRateLimitMiddleware:
    """Bound repeated public auth mutations by source IP.

    Vercel overwrites ``x-forwarded-for`` at its edge, so production can safely
    use that value as the public client IP. Outside Vercel we deliberately ignore
    forwarded headers and fall back to the ASGI client address.

    State is intentionally process-local: this adds a cheap application barrier
    against burst abuse but does not pretend to replace distributed edge limits.
    The middleware is enabled automatically on Vercel and can be opted into on
    other runtimes with ``VEZMORA_AUTH_RATE_LIMIT=true``.
    """

    def __init__(self, app: Any, *, clock=time.monotonic) -> None:
        self.app = app
        self._clock = clock
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    @staticmethod
    def _header(scope: dict[str, Any], name: bytes) -> str | None:
        values = [
            value
            for raw_name, value in scope.get("headers") or []
            if raw_name.lower() == name
        ]
        if len(values) != 1:
            return None
        try:
            return values[0].decode("latin-1").strip()
        except UnicodeDecodeError:
            return None

    @classmethod
    def _client_ip(cls, scope: dict[str, Any]) -> str:
        if os.getenv("VERCEL"):
            forwarded = cls._header(scope, b"x-forwarded-for")
            if forwarded:
                # Vercel supplies the public client IP here. Be defensive if a
                # future proxy representation contains a comma-separated chain.
                candidate = forwarded.split(",", 1)[0].strip()
                if candidate:
                    return candidate[:128]
        client = scope.get("client")
        if isinstance(client, (tuple, list)) and client:
            return str(client[0])[:128]
        return "unknown"

    def _allow(self, path: str, client_ip: str, limit: _Limit) -> tuple[bool, int]:
        now = float(self._clock())
        cutoff = now - limit.window_seconds
        key = (path, client_ip)
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit.max_requests:
                retry_after = max(1, int(limit.window_seconds - (now - events[0])))
                return False, retry_after
            events.append(now)
            # Opportunistic cleanup prevents unbounded stale-key growth without
            # requiring a background task in serverless runtimes.
            if len(self._events) > 4096:
                stale = [
                    existing_key
                    for existing_key, existing_events in self._events.items()
                    if not existing_events or existing_events[-1] <= cutoff
                ]
                for existing_key in stale[:1024]:
                    self._events.pop(existing_key, None)
            return True, 0

    async def __call__(self, scope: dict[str, Any], receive, send) -> None:
        if not _rate_limit_enabled():
            await self.app(scope, receive, send)
            return
        if scope.get("type") != "http" or str(scope.get("method") or "").upper() != "POST":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path") or "").rstrip("/") or "/"
        limit = _LIMITS.get(path)
        if limit is None:
            await self.app(scope, receive, send)
            return

        client_ip = self._client_ip(scope)
        allowed, retry_after = self._allow(path, client_ip, limit)
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many authentication requests. Try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "Cache-Control": "no-store",
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def install_auth_rate_limit(app) -> None:
    """Install the auth limiter once so repeated app setup cannot double-count requests."""
    if getattr(app.state, "vexmera_auth_rate_limit_installed", False):
        return
    app.add_middleware(AuthRateLimitMiddleware)
    app.state.vexmera_auth_rate_limit_installed = True
