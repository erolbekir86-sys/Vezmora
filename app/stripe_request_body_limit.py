from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from .api_request_body_limit import ApiRequestBodyLimitMiddleware
from .stripe_billing import MAX_WEBHOOK_PAYLOAD_BYTES

_STRIPE_WEBHOOK_PATHS = frozenset({"/api/billing/webhook", "/api/billing/webhook/"})


class _StripeWebhookPayloadTooLarge(Exception):
    pass


class _InvalidContentLength(Exception):
    pass


class StripeWebhookBodyLimitMiddleware:
    """Reject oversized Stripe webhook bodies before buffering them in memory.

    ``parse_webhook`` still enforces the same limit as a defense-in-depth check.
    This middleware moves the boundary to the ASGI receive stream so requests
    without a trustworthy Content-Length header cannot bypass the memory guard.
    """

    def __init__(self, app: Any, max_bytes: int = MAX_WEBHOOK_PAYLOAD_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    @staticmethod
    def _content_length(scope: dict[str, Any]) -> int | None:
        values: list[bytes] = []
        for raw_name, raw_value in scope.get("headers") or []:
            if raw_name.lower() == b"content-length":
                values.append(raw_value)

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

    async def __call__(self, scope: dict[str, Any], receive, send) -> None:
        if scope.get("type") != "http" or scope.get("path") not in _STRIPE_WEBHOOK_PATHS:
            await self.app(scope, receive, send)
            return

        try:
            content_length = self._content_length(scope)
        except _InvalidContentLength:
            response = JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length"},
            )
            await response(scope, receive, send)
            return

        if content_length is not None and content_length > self.max_bytes:
            response = JSONResponse(
                status_code=413,
                content={"detail": "Stripe webhook payload is too large"},
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
                    raise _StripeWebhookPayloadTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _StripeWebhookPayloadTooLarge:
            response = JSONResponse(
                status_code=413,
                content={"detail": "Stripe webhook payload is too large"},
            )
            await response(scope, receive, send)


def install_stripe_webhook_body_limit(app) -> None:
    # Ordinary JSON mutations get a separate request-body memory ceiling while
    # Stripe retains its dedicated limiter and signature-verification contract.
    app.add_middleware(ApiRequestBodyLimitMiddleware)
    app.add_middleware(StripeWebhookBodyLimitMiddleware)
