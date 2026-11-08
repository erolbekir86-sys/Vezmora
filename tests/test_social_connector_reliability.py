import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

from app import connectors
from app.secret_redaction import redact_sensitive_text


def transport(monkeypatch, handler):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(connectors.httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))


def test_linkedin_oauth_retains_account_settings_entered_before_connect(monkeypatch):
    monkeypatch.setattr(connectors, "consume_oauth_state", lambda *args: {"workspace_id": 7})
    monkeypatch.setattr(connectors, "get_connector", lambda *args: {"metadata": {"ad_account_id": "123456"}})
    monkeypatch.setattr(connectors, "encrypt_json", lambda value: "encrypted")
    saved = []
    monkeypatch.setattr(connectors, "save_connector", lambda **kwargs: saved.append(kwargs))
    transport(monkeypatch, lambda request: httpx.Response(200, json={"access_token": "test-token", "expires_in": 3600}))
    asyncio.run(connectors.linkedin_callback("test-code", "valid-state"))
    assert saved[0]["metadata"]["ad_account_id"] == "123456"
    assert saved[0]["metadata"]["read_only"] is True


def instagram_connected(monkeypatch):
    monkeypatch.setattr(connectors, "get_connector", lambda *args, **kwargs: {
        "status": "connected", "external_id": "12345", "secret_blob": "encrypted", "metadata": {},
    })
    monkeypatch.setattr(connectors, "decrypt_json", lambda *args: {"access_token": "private-test-token"})
    monkeypatch.setattr(connectors, "add_notification", lambda *args: None)


def test_instagram_pagination_uses_fixed_graph_url_and_opaque_cursor(monkeypatch):
    instagram_connected(monkeypatch)
    calls = []
    saved = []
    monkeypatch.setattr(connectors, "update_connector_metadata", lambda *args: saved.append(args))

    def handler(request):
        calls.append(request)
        assert request.url.host == "graph.facebook.com"
        if request.url.path.endswith("/media"):
            if "after" not in request.url.params:
                return httpx.Response(200, json={"data": [], "paging": {"next": "https://attacker.test/leak?access_token=private-test-token", "cursors": {"after": "safe-cursor"}}})
            assert request.url.params["after"] == "safe-cursor"
            return httpx.Response(200, json={"data": []})
        return httpx.Response(200, json={"followers_count": 10, "media_count": 0})

    transport(monkeypatch, handler)
    result = asyncio.run(connectors.sync_instagram(7))
    assert len(calls) == 3
    assert result["read_only"] is True
    assert len(saved) == 1


@pytest.mark.parametrize("cursor", ["", "repeated-cursor"])
def test_instagram_incomplete_or_excessive_pages_do_not_replace_previous_report(monkeypatch, cursor):
    instagram_connected(monkeypatch)
    monkeypatch.setattr(connectors, "update_connector_metadata", lambda *args: pytest.fail("Previous report must remain"))

    def handler(request):
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"data": [], "paging": {"next": "https://graph.facebook.com/next", "cursors": {"after": cursor}}})
        return httpx.Response(200, json={})

    transport(monkeypatch, handler)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(connectors.sync_instagram(7))
    assert exc.value.status_code in {409, 502}


def test_instagram_does_not_silently_select_an_unintended_business_account(monkeypatch):
    monkeypatch.setattr(connectors, "consume_oauth_state", lambda *args: {"workspace_id": 7})
    monkeypatch.setattr(connectors, "save_connector", lambda *args, **kwargs: pytest.fail("Owner must select the account"))

    def handler(request):
        if request.url.path.endswith("/oauth/access_token"):
            return httpx.Response(200, json={"access_token": "private-test-token"})
        return httpx.Response(200, json={"data": [{"instagram_business_account": {"id": "123"}}, {"instagram_business_account": {"id": "456"}}]})

    transport(monkeypatch, handler)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(connectors.instagram_callback("test-code", "valid-state"))
    assert exc.value.status_code == 409


def test_new_social_secrets_and_tiktok_auth_code_are_redacted(monkeypatch):
    for key in ["LINKEDIN_CLIENT_SECRET", "SHOPIFY_CLIENT_SECRET", "TIKTOK_APP_SECRET"]:
        monkeypatch.setenv(key, key + "-private-value")
        assert key + "-private-value" not in redact_sensitive_text(key + "-private-value")
    text = redact_sensitive_text("https://vexmera.com/callback?auth_code=one-time-private&state=private-state")
    assert "one-time-private" not in text
    assert "private-state" not in text
