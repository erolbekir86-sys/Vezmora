from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from app import connectors
from app.models import ConnectorSettings


def test_linkedin_readiness_fails_closed_without_configuration(monkeypatch):
    for name in ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_REDIRECT_URI"):
        monkeypatch.delenv(name, raising=False)

    readiness = connectors.connector_readiness()

    assert readiness["linkedin"]["configured"] is False
    assert readiness["linkedin"]["label"] == "LinkedIn Ads"
    assert "LinkedIn Advertising API approval" in readiness["linkedin"]["requirements"]


def test_linkedin_oauth_requests_read_only_advertising_scopes(monkeypatch):
    captured = {}
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "linkedin-client")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "linkedin-secret")
    monkeypatch.setenv(
        "LINKEDIN_REDIRECT_URI",
        "https://vexmera.example/api/connectors/linkedin/callback",
    )
    monkeypatch.setattr(
        connectors,
        "save_oauth_state",
        lambda state, user_id, workspace_id, provider: captured.update(
            state=state, user_id=user_id, workspace_id=workspace_id, provider=provider
        ),
    )

    url = connectors.linkedin_authorization_url(7, 3)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    scopes = set(query["scope"][0].split())

    assert parsed.scheme == "https"
    assert parsed.netloc == "www.linkedin.com"
    assert parsed.path == "/oauth/v2/authorization"
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["linkedin-client"]
    assert query["redirect_uri"] == ["https://vexmera.example/api/connectors/linkedin/callback"]
    assert scopes == {"r_ads", "r_ads_reporting"}
    assert captured["provider"] == "linkedin"
    assert all("write" not in scope.lower() and not scope.lower().startswith("rw_") for scope in scopes)


def test_linkedin_headers_are_versioned_and_restli_safe(monkeypatch):
    monkeypatch.setenv("LINKEDIN_API_VERSION", "202608")

    headers = connectors._linkedin_headers("test-token")

    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Linkedin-Version"] == "202608"
    assert headers["X-Restli-Protocol-Version"] == "2.0.0"


def test_linkedin_sync_fails_closed_without_connected_account(monkeypatch):
    monkeypatch.setattr(connectors, "get_connector", lambda *args, **kwargs: None)

    with pytest.raises(HTTPException) as exc_info:
        import asyncio
        asyncio.run(connectors.sync_linkedin(9, 30))

    assert exc_info.value.status_code == 409
    assert "connect linkedin" in str(exc_info.value.detail).lower()


def test_linkedin_ad_account_setting_is_supported_and_normalized():
    settings = ConnectorSettings(
        linkedin_ad_account_id="  urn:li:sponsoredAccount:123456789  "
    )

    assert settings.linkedin_ad_account_id == "urn:li:sponsoredAccount:123456789"


def test_linkedin_is_in_sync_all_source():
    assert "linkedin" in connectors.sync_all.__code__.co_consts
