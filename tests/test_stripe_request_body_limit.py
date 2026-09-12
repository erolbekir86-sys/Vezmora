from __future__ import annotations

import asyncio
import json

from app.stripe_request_body_limit import StripeWebhookBodyLimitMiddleware


def _scope(*, path: str = "/api/billing/webhook", content_length: str | None = None):
    headers = []
    if content_length is not None:
        headers.append((b"content-length", content_length.encode("ascii")))
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    }


def _run_request(messages, *, content_length: str | None = None, path: str = "/api/billing/webhook", max_bytes: int = 5):
    sent = []
    called = {"inner": False}
    queue = list(messages)

    async def receive():
        return queue.pop(0)

    async def send(message):
        sent.append(message)

    async def inner(scope, receive_inner, send_inner):
        called["inner"] = True
        while True:
            message = await receive_inner()
            if message["type"] != "http.request" or not message.get("more_body", False):
                break
        await send_inner({"type": "http.response.start", "status": 204, "headers": []})
        await send_inner({"type": "http.response.body", "body": b""})

    middleware = StripeWebhookBodyLimitMiddleware(inner, max_bytes=max_bytes)
    asyncio.run(middleware(_scope(path=path, content_length=content_length), receive, send))
    return sent, called["inner"]


def _response(sent):
    start = next(message for message in sent if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return start["status"], json.loads(body) if body else None


def test_rejects_oversized_declared_webhook_before_inner_app_reads_body():
    sent, inner_called = _run_request(
        [{"type": "http.request", "body": b"ignored", "more_body": False}],
        content_length="6",
    )

    assert inner_called is False
    assert _response(sent) == (413, {"detail": "Stripe webhook payload is too large"})


def test_rejects_chunked_webhook_when_cumulative_body_crosses_limit():
    sent, inner_called = _run_request(
        [
            {"type": "http.request", "body": b"abc", "more_body": True},
            {"type": "http.request", "body": b"def", "more_body": False},
        ]
    )

    assert inner_called is True
    assert _response(sent) == (413, {"detail": "Stripe webhook payload is too large"})


def test_allows_webhook_at_limit_and_does_not_affect_other_paths():
    webhook_sent, webhook_called = _run_request(
        [{"type": "http.request", "body": b"abcde", "more_body": False}],
        content_length="5",
    )
    other_sent, other_called = _run_request(
        [{"type": "http.request", "body": b"far-too-large", "more_body": False}],
        content_length="13",
        path="/api/feedback",
    )

    assert webhook_called is True
    assert _response(webhook_sent) == (204, None)
    assert other_called is True
    assert _response(other_sent) == (204, None)
