from __future__ import annotations

from fastapi.testclient import TestClient

import main as production_entrypoint


def test_browser_security_headers_are_applied_to_public_responses(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VEZMORA_APP_URL", raising=False)

    with TestClient(production_entrypoint.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert "strict-transport-security" not in response.headers


def test_health_diagnostics_are_no_store_and_https_gets_hsts(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    with TestClient(production_entrypoint.app) as client:
        response = client.get("/health/runtime")

    assert response.status_code == 200
    cache_control = response.headers["cache-control"]
    assert "no-store" in cache_control
    assert "no-cache" in cache_control
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_beta_readiness_is_not_cacheable(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    with TestClient(production_entrypoint.app) as client:
        response = client.get("/health/beta-readiness")

    assert response.status_code == 200
    cache_control = response.headers["cache-control"]
    assert "no-store" in cache_control
    assert "no-cache" in cache_control
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
