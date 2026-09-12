from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

MAX_API_REQUEST_BODY_BYTES = 1024 * 1024
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_SKIP_PATHS = frozenset({"/api/billing/webhook", "/api/billing/webhook/"})


class _ApiPayloadTooLarge(Exception):
    pass


class _InvalidContentLength(Exception):
    pass


class ApiRequestBodyLimitMiddleware:
    """Bound ordinary API request bodies before FastAPI buffers/parses them.

    Vexmera's authenticated JSON inputs are all far smaller than this ceiling.
    Stripe webhooks keep their dedicated limiter so their existing signature and
    error contract remain independent.
    """

    def __init__(self, app: Any, max_bytes: int = MAX_API_REQUEST_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    @staticmethod
    def _content_length(scope: dict[str, Any]) -> int | None:
        values = [
            raw_value
            for raw_name, raw_value in (scope.get("headers") or [])
            if raw_name.lower() == b"content-length"
        ]
        if not values:
            return None
        if len(values) != 1:
            raise _InvalidContentLength
        try:
            value = int(values[0].decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            raise _InvalidContentLength from None
        if value < 0:
            raise _InvalidContentLength
        return value

    @staticmethod
    def _applies(scope: dict[str, Any]) -> bool:
        path = str(scope.get("path") or "")
        method = str(scope.get("method") or "").upper()
        return (
            scope.get("type") == "http"
            and method in _BODY_METHODS
            and (path == "/api" or path.startswith("/api/"))
            and path not in _SKIP_PATHS
        )

    async def __call__(self, scope: dict[str, Any], receive, send) -> None:
        if not self._applies(scope):
            await self.app(scope, receive, send)
            return

        try:
            content_length = self._content_length(scope)
        except _InvalidContentLength:
            response = JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length"},
                headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return

        if content_length is not None and content_length > self.max_bytes:
            response = JSONResponse(
                status_code=413,
                content={"detail": "API request payload is too large"},
                headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"") or b""
                received += len(body)
                if received > self.max_bytes:
                    raise _ApiPayloadTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _ApiPayloadTooLarge:
            response = JSONResponse(
                status_code=413,
                content={"detail": "API request payload is too large"},
                headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
