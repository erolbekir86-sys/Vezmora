from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from app import connectors


def test_meta_connector_readiness_requires_all_credentials(monkeypatch):
    for name in ("META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"):
        monkeypatch.delenv(name, raising=False)

    assert connectors.connector_readiness()["meta"]["configured"] is False

    monkeypatch.setenv("META_APP_ID", "123456")
    monkeypatch.setenv("META_APP_SECRET", "test-only-secret")
    monkeypatch.setenv(
        "META_REDIRECT_URI",
        "https://app.example.test/api/connectors/meta/callback",
    )

    assert connectors.connector_readiness()["meta"]["configured"] is True


def test_meta_authorization_url_is_read_only_by_default(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.setenv("META_APP_ID", "123456")
    monkeypatch.setenv(
        "META_REDIRECT_URI",
        "https://app.example.test/api/connectors/meta/callback",
    )
    monkeypatch.setattr(
        connectors,
        "save_oauth_state",
        lambda state, user_id, workspace_id, provider: captured.update(
            {
                "state": state,
                "user_id": user_id,
                "workspace_id": workspace_id,
                "provider": provider,
            }
        ),
    )

    url = connectors.meta_authorization_url(workspace_id=7, user_id=3)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "www.facebook.com"
    assert query["client_id"] == ["123456"]
    assert query["redirect_uri"] == [
        "https://app.example.test/api/connectors/meta/callback"
    ]
    assert query["response_type"] == ["code"]
    assert query["state"] == [captured["state"]]
    assert captured["workspace_id"] == 7
    assert captured["user_id"] == 3
    assert captured["provider"] == "meta"

    scopes = set(query["scope"][0].split(","))
    assert "ads_read" in scopes
    # Private beta must not request write access unless the deployment
    # explicitly enables the execution scope before module import.
    if "ads_management" in scopes:
        pytest.fail("Meta OAuth unexpectedly requested ads_management")


def test_meta_callback_rejects_invalid_state_without_network_call(monkeypatch):
    monkeypatch.setattr(connectors, "consume_oauth_state", lambda state, provider: None)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(connectors.meta_callback("fake-code", "invalid-state"))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired OAuth state"
