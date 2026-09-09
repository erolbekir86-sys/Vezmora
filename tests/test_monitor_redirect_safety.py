from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app import monitor


class _FakeResponse:
    def __init__(self, status_code: int, url: str, *, location: str | None = None, text: str = "") -> None:
        self.status_code = status_code
        self.url = url
        self.text = text
        self.headers: dict[str, str] = {"content-type": "text/html"}
        if location is not None:
            self.headers["location"] = location


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

    async def get(self, url: str, *, headers: dict[str, str]) -> _FakeResponse:
        assert headers["User-Agent"].startswith("VezmoraBot/")
        self.requested_urls.append(url)
        return self.responses.pop(0)


def _reset_fake_client(*responses: _FakeResponse) -> None:
    _FakeClient.responses = list(responses)
    _FakeClient.requested_urls = []
    _FakeClient.follow_redirects_values = []


def test_competitor_fetch_rejects_redirect_to_private_address(monkeypatch):
    _reset_fake_client(
        _FakeResponse(
            302,
            "https://public.example/start",
            location="http://169.254.169.254/latest/meta-data/",
        )
    )
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
    assert _FakeClient.requested_urls == [
        "https://public.example/start",
        "https://public.example/landing",
    ]
    assert "https://public.example/landing" in checked
    assert _FakeClient.follow_redirects_values == [False]


def test_safe_public_url_rejects_common_local_targets():
    assert monitor._safe_public_url("http://127.0.0.1/admin") is False
    assert monitor._safe_public_url("http://169.254.169.254/latest/meta-data/") is False
    assert monitor._safe_public_url("http://localhost/internal") is False
    assert monitor._safe_public_url("file:///etc/passwd") is False
