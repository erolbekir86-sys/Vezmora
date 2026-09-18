from __future__ import annotations

import hashlib
import hmac
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from fastapi import HTTPException

from app import connectors


def test_instagram_and_shopify_readiness_fail_closed(monkeypatch):
    for name in (
        "META_APP_ID",
        "META_APP_SECRET",
        "INSTAGRAM_REDIRECT_URI",
        "SHOPIFY_CLIENT_ID",
        "SHOPIFY_CLIENT_SECRET",
        "SHOPIFY_REDIRECT_URI",
    ):
        monkeypatch.delenv(name, raising=False)

    readiness = connectors.connector_readiness()
    assert readiness["instagram"]["configured"] is False
    assert readiness["shopify"]["configured"] is False


def test_instagram_oauth_requests_read_only_professional_account_scopes(monkeypatch):
    captured = {}
    monkeypatch.setenv("META_APP_ID", "123456")
    monkeypatch.setenv("INSTAGRAM_REDIRECT_URI", "https://app.example.test/api/connectors/instagram/callback")
    monkeypatch.setattr(
        connectors,
        "save_oauth_state",
        lambda state, user_id, workspace_id, provider: captured.update(
            state=state, user_id=user_id, workspace_id=workspace_id, provider=provider
        ),
    )

    url = connectors.instagram_authorization_url(7, 3)
    query = parse_qs(urlparse(url).query)
    scopes = set(query["scope"][0].split(","))

    assert urlparse(url).netloc == "www.facebook.com"
    assert captured["provider"] == "instagram"
    assert scopes == {
        "pages_show_list",
        "pages_read_engagement",
        "instagram_basic",
        "instagram_manage_insights",
    }
    assert "instagram_content_publish" not in scopes


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("vexmera-demo", "vexmera-demo.myshopify.com"),
        ("vexmera-demo.myshopify.com", "vexmera-demo.myshopify.com"),
        ("https://vexmera-demo.myshopify.com/admin", "vexmera-demo.myshopify.com"),
    ],
)
def test_shopify_shop_normalization_accepts_only_myshopify_hosts(value, expected):
    assert connectors._normalize_shopify_shop(value) == expected


@pytest.mark.parametrize("value", ["example.com", "localhost", "127.0.0.1", "shop.myshopify.com.attacker.test"])
def test_shopify_shop_normalization_rejects_untrusted_hosts(value):
    with pytest.raises(HTTPException) as exc_info:
        connectors._normalize_shopify_shop(value)
    assert exc_info.value.status_code == 400


def test_shopify_oauth_is_read_only_and_stores_state(monkeypatch):
    captured = {}
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SHOPIFY_REDIRECT_URI", "https://app.example.test/api/connectors/shopify/callback")
    monkeypatch.setattr(
        connectors,
        "save_oauth_state",
        lambda state, user_id, workspace_id, provider: captured.update(
            state=state, user_id=user_id, workspace_id=workspace_id, provider=provider
        ),
    )

    url = connectors.shopify_authorization_url(8, 4, "vexmera-demo")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "vexmera-demo.myshopify.com"
    assert parsed.path == "/admin/oauth/authorize"
    assert query["scope"] == ["read_orders"]
    assert captured["provider"] == "shopify"
    assert all(not scope.startswith("write_") for scope in connectors.SHOPIFY_SCOPES)


def test_shopify_callback_hmac_uses_constant_time_verifiable_digest(monkeypatch):
    secret = "test-shopify-secret"
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", secret)
    query = {
        "code": "abc123",
        "shop": "vexmera-demo.myshopify.com",
        "state": "safe_state-123",
        "timestamp": "1789745000",
    }
    message = urlencode(sorted(query.items()))
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    signed = {**query, "hmac": digest}

    assert connectors._verify_shopify_hmac(signed, digest) is True
    assert connectors._verify_shopify_hmac(signed, "0" * 64) is False


def test_new_connectors_are_in_sync_all_source():
    source = connectors.sync_all.__code__
    assert "instagram" in source.co_consts
    assert "shopify" in source.co_consts
