from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI

from app.auth_rate_limit import AuthRateLimitMiddleware, _Limit, install_auth_rate_limit


def _scope(*, path: str = "/api/auth/login", ip: str = "203.0.113.9", forwarded: str | None = None):
    headers = []
    if forwarded is not None:
        headers.append((b"x-forwarded-for", forwarded.encode("ascii")))
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
        "client": (ip, 12345),
        "server": ("testserver", 443),
    }


def _request(middleware: AuthRateLimitMiddleware, scope):
    sent = []
    called = {"inner": False}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    async def run():
        await middleware(scope, receive, send)

    asyncio.run(run())
    if any(message["type"] == "http.response.start" for message in sent):
        start = next(message for message in sent if message["type"] == "http.response.start")
        body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
        return start, json.loads(body) if body else None
    return None, called["inner"]


def _middleware(*, clock):
    async def inner(scope, receive, send):
        del scope, receive
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    return AuthRateLimitMiddleware(inner, clock=clock)


def test_limit_rejects_burst_and_allows_again_after_window(monkeypatch):
    del monkeypatch
    now = [100.0]
    middleware = _middleware(clock=lambda: now[0])
    path = "/api/auth/login"
    middleware_limit = _Limit(max_requests=2, window_seconds=10)

    assert middleware._allow(path, "203.0.113.9", middleware_limit) == (True, 0)
    assert middleware._allow(path, "203.0.113.9", middleware_limit) == (True, 0)
    allowed, retry_after = middleware._allow(path, "203.0.113.9", middleware_limit)
    assert allowed is False
    assert 1 <= retry_after <= 10

    now[0] = 111.0
    assert middleware._allow(path, "203.0.113.9", middleware_limit) == (True, 0)


def test_vercel_uses_overwritten_forwarded_ip(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    scope = _scope(ip="10.0.0.7", forwarded="198.51.100.20")
    assert AuthRateLimitMiddleware._client_ip(scope) == "198.51.100.20"


def test_non_vercel_ignores_spoofable_forwarded_ip(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    scope = _scope(ip="127.0.0.1", forwarded="198.51.100.20")
    assert AuthRateLimitMiddleware._client_ip(scope) == "127.0.0.1"


def test_rate_limit_response_is_429_no_store_with_retry_after(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    middleware = _middleware(clock=lambda: 100.0)
    from app import auth_rate_limit as module

    monkeypatch.setitem(module._LIMITS, "/api/auth/login", _Limit(max_requests=1, window_seconds=30))

    first_start, _ = _request(middleware, _scope(forwarded="198.51.100.30"))
    assert first_start["status"] == 204

    second_start, payload = _request(middleware, _scope(forwarded="198.51.100.30"))
    headers = {key.decode().lower(): value.decode() for key, value in second_start["headers"]}
    assert second_start["status"] == 429
    assert payload == {"detail": "Too many authentication requests. Try again later."}
    assert headers["cache-control"] == "no-store"
    assert int(headers["retry-after"]) >= 1


def test_unrelated_route_is_not_limited(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    middleware = _middleware(clock=lambda: 100.0)
    start, _ = _request(middleware, _scope(path="/api/feedback", forwarded="198.51.100.40"))
    assert start["status"] == 204


def test_install_auth_rate_limit_is_idempotent() -> None:
    app = FastAPI()

    install_auth_rate_limit(app)
    middleware_count = len(app.user_middleware)
    install_auth_rate_limit(app)

    assert len(app.user_middleware) == middleware_count
    assert app.state.vexmera_auth_rate_limit_installed is True
