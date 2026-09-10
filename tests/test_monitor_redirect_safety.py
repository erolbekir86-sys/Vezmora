from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app import monitor


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        url: str,
        *,
        location: str | None = None,
        text: str = "",
        chunks: list[bytes] | None = None,
        content_length: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self._chunks = chunks if chunks is not None else [text.encode("utf-8")]
        self.headers: dict[str, str] = {"content-type": "text/html"}
        if location is not None:
            self.headers["location"] = location
        if content_length is not None:
            self.headers["content-length"] = str(content_length)
        self.request = httpx.Request("GET", url)
        self.extensions: dict[str, object] = {}
        self.body_iterated = False

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def aiter_bytes(self):
        self.body_iterated = True
        for chunk in self._chunks:
            yield chunk


class _FakeClient:
    responses: list[_FakeResponse] = []
    requested_urls: list[str] = []
    follow_redirects_values: list[bool] = []

    def __init__(self, *, timeout: int, follow_redirects: bool) -> None:
        assert timeout == 15
        self.follow_redirects_values.append(follow_redirects)

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def stream(self, method: str, url: str, *, headers: dict[str, str]) -> _FakeResponse:
        assert method == "GET"
        assert headers["User-Agent"].startswith("VezmoraBot/")
        self.requested_urls.append(url)
        return self.responses.pop(0)


def _reset_fake_client(*responses: _FakeResponse) -> None:
    _FakeClient.responses = list(responses)
    _FakeClient.requested_urls = []
    _FakeClient.follow_redirects_values = []


def test_competitor_fetch_rejects_redirect_to_private_address(monkeypatch):
    response = _FakeResponse(
        302,
        "https://public.example/start",
        location="http://169.254.169.254/latest/meta-data/",
    )
    _reset_fake_client(response)
    monkeypatch.setattr(monitor.httpx, "AsyncClient", _FakeClient)
    monkeypatch.setattr(
        monitor,
        "_safe_public_url",
        lambda url: not url.startswith("http://169.254.169.254"),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            monitor._fetch_public_page(
                "https://public.example/start",
                {"User-Agent": "VezmoraBot/0.4 test"},
            )
        )

    assert exc_info.value.status_code == 400
    assert "non-public" in str(exc_info.value.detail)
    assert response.body_iterated is False
    assert _FakeClient.requested_urls == ["https://public.example/start"]
    assert _FakeClient.follow_redirects_values == [False]


def test_competitor_fetch_validates_and_follows_public_relative_redirect(monkeypatch):
    _reset_fake_client(
        _FakeResponse(302, "https://public.example/start", location="/landing"),
        _FakeResponse(200, "https://public.example/landing", text="<html>ok</html>"),
    )
    monkeypatch.setattr(monitor.httpx, "AsyncClient", _FakeClient)
    checked: list[str] = []

    def fake_safe_public_url(url: str) -> bool:
        checked.append(url)
        return url.startswith("https://public.example/")

    monkeypatch.setattr(monitor, "_safe_public_url", fake_safe_public_url)

    response = asyncio.run(
        monitor._fetch_public_page(
            "https://public.example/start",
            {"User-Agent": "VezmoraBot/0.4 test"},
        )
    )

    assert response.status_code == 200
    assert response.text == "<html>ok</html>"
    assert _FakeClient.requested_urls == [
        "https://public.example/start",
        "https://public.example/landing",
    ]
    assert "https://public.example/landing" in checked
    assert _FakeClient.follow_redirects_values == [False]


def test_declared_oversized_competitor_page_is_rejected_before_body_read(monkeypatch):
    response = _FakeResponse(
        200,
        "https://public.example/huge",
        chunks=[b"small-body"],
        content_length=monitor._MAX_RESPONSE_BYTES + 1,
    )
    _reset_fake_client(response)
    monkeypatch.setattr(monitor.httpx, "AsyncClient", _FakeClient)
    monkeypatch.setattr(monitor, "_safe_public_url", lambda url: True)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            monitor._fetch_public_page(
                "https://public.example/huge",
                {"User-Agent": "VezmoraBot/0.4 test"},
            )
        )

    assert exc_info.value.status_code == 413
    assert "too large" in str(exc_info.value.detail)
    assert response.body_iterated is False


def test_chunked_oversized_competitor_page_is_rejected_at_stream_limit(monkeypatch):
    response = _FakeResponse(
        200,
        "https://public.example/chunked",
        chunks=[b"a" * monitor._MAX_RESPONSE_BYTES, b"b"],
    )
    _reset_fake_client(response)
    monkeypatch.setattr(monitor.httpx, "AsyncClient", _FakeClient)
    monkeypatch.setattr(monitor, "_safe_public_url", lambda url: True)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            monitor._fetch_public_page(
                "https://public.example/chunked",
                {"User-Agent": "VezmoraBot/0.4 test"},
            )
        )

    assert exc_info.value.status_code == 413
    assert "too large" in str(exc_info.value.detail)
    assert response.body_iterated is True


def test_safe_public_url_rejects_non_global_and_credentialed_targets():
    assert monitor._safe_public_url("http://127.0.0.1/admin") is False
    assert monitor._safe_public_url("http://169.254.169.254/latest/meta-data/") is False
    assert monitor._safe_public_url("http://100.64.0.1/internal") is False
    assert monitor._safe_public_url("http://localhost/internal") is False
    assert monitor._safe_public_url("http://user:password@8.8.8.8/private") is False
    assert monitor._safe_public_url("file:///etc/passwd") is False
    assert monitor._safe_public_url("https://8.8.8.8/") is True
