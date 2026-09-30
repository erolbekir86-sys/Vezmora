from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_public_connector_health_exposes_boolean_readiness_only(monkeypatch) -> None:
    values = {
        "GOOGLE_CLIENT_ID": "google-client-private",
        "GOOGLE_CLIENT_SECRET": "google-secret-private",
        "GOOGLE_REDIRECT_URI": "https://example.test/google",
        "META_APP_ID": "meta-app-private",
        "META_APP_SECRET": "meta-secret-private",
        "META_REDIRECT_URI": "https://example.test/meta",
        "INSTAGRAM_REDIRECT_URI": "https://example.test/instagram",
        "SHOPIFY_CLIENT_ID": "shopify-client-private",
        "SHOPIFY_CLIENT_SECRET": "shopify-secret-private",
        "SHOPIFY_REDIRECT_URI": "https://example.test/shopify",
        "LINKEDIN_CLIENT_ID": "linkedin-client-private",
        "LINKEDIN_CLIENT_SECRET": "linkedin-secret-private",
        "LINKEDIN_REDIRECT_URI": "https://example.test/linkedin",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    with TestClient(app) as client:
        response = client.get("/health/connectors")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["phase"] == "private_beta"
    assert payload["providers"]["instagram"]["runtime_configured"] is True
    assert payload["providers"]["shopify"]["runtime_configured"] is True
    assert payload["providers"]["linkedin"]["runtime_configured"] is True

    rendered = response.text
    for secret in values.values():
        assert secret not in rendered


def test_public_connector_health_reports_missing_provider_configuration(monkeypatch) -> None:
    for name in (
        "INSTAGRAM_REDIRECT_URI",
        "SHOPIFY_CLIENT_ID",
        "SHOPIFY_CLIENT_SECRET",
        "SHOPIFY_REDIRECT_URI",
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_REDIRECT_URI",
    ):
        monkeypatch.delenv(name, raising=False)

    with TestClient(app) as client:
        response = client.get("/health/connectors")

    payload = response.json()
    assert payload["providers"]["instagram"]["runtime_configured"] is False
    assert payload["providers"]["shopify"]["runtime_configured"] is False
    assert payload["providers"]["linkedin"]["runtime_configured"] is False
