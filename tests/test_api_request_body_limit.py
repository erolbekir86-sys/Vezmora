from __future__ import annotations

import asyncio
import json

from app.api_request_body_limit import ApiRequestBodyLimitMiddleware


def _scope(
    *,
    path: str = "/api/auth/login",
    method: str = "POST",
    content_length: str | None = None,
    extra_headers: list[tuple[bytes, bytes]] | None = None,
):
    headers = list(extra_headers or [])
    if content_length is not None:
        headers.append((b"content-length", content_length.encode("ascii")))
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    }


def _run_request(
    messages,
    *,
    path: str = "/api/auth/login",
    method: str = "POST",
    content_length: str | None = None,
    extra_headers: list[tuple[bytes, bytes]] | None = None,
    max_bytes: int = 5,
):
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

    middleware = ApiRequestBodyLimitMiddleware(inner, max_bytes=max_bytes)
    asyncio.run(
        middleware(
            _scope(
                path=path,
                method=method,
                content_length=content_length,
                extra_headers=extra_headers,
            ),
            receive,
            send,
        )
    )
    return sent, called["inner"]


def _response(sent):
    start = next(message for message in sent if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return start["status"], json.loads(body) if body else None


def test_rejects_oversized_declared_api_body_before_inner_app_reads_it():
    sent, inner_called = _run_request(
        [{"type": "http.request", "body": b"ignored", "more_body": False}],
        content_length="6",
    )

    assert inner_called is False
    assert _response(sent) == (413, {"detail": "API request payload is too large"})


def test_rejects_chunked_api_body_when_cumulative_size_crosses_limit():
    sent, inner_called = _run_request(
        [
            {"type": "http.request", "body": b"abc", "more_body": True},
            {"type": "http.request", "body": b"def", "more_body": False},
        ]
    )

    assert inner_called is True
    assert _response(sent) == (413, {"detail": "API request payload is too large"})


def test_rejects_invalid_or_ambiguous_content_length():
    for value, extra_headers in (
        ("not-a-number", None),
        ("-1", None),
        ("3", [(b"content-length", b"3")]),
    ):
        sent, inner_called = _run_request(
            [{"type": "http.request", "body": b"abc", "more_body": False}],
            content_length=value,
            extra_headers=extra_headers,
        )

        assert inner_called is False
        assert _response(sent) == (400, {"detail": "Invalid Content-Length"})


def test_allows_api_body_at_limit():
    sent, inner_called = _run_request(
        [{"type": "http.request", "body": b"abcde", "more_body": False}],
        content_length="5",
    )

    assert inner_called is True
    assert _response(sent) == (204, None)


def test_does_not_interfere_with_get_static_or_stripe_webhook_paths():
    cases = (
        {"path": "/api/dashboard", "method": "GET"},
        {"path": "/static/app.js", "method": "POST"},
        {"path": "/api/billing/webhook", "method": "POST"},
    )
    for case in cases:
        sent, inner_called = _run_request(
            [{"type": "http.request", "body": b"far-too-large", "more_body": False}],
            content_length="13",
            **case,
        )

        assert inner_called is True
        assert _response(sent) == (204, None)
