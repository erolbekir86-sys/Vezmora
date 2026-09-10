from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

import app.main as main_module
import app.store as store
from app.security_headers import install_security_headers


def test_vexmera_responses_include_low_risk_browser_hardening(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "headers.db")

    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["x-permitted-cross-domain-policies"] == "none"
    assert "strict-transport-security" not in response.headers


def test_hsts_is_added_for_vercel_https_runtime(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    app = FastAPI()

    @app.get("/")
    def root():
        return {"ok": True}

    install_security_headers(app)
    with TestClient(app) as client:
        response = client.get("/")

    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"


def test_https_app_url_enables_hsts_without_vercel(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "https://app.example.test")
    app = FastAPI()

    @app.get("/")
    def root():
        return {"ok": True}

    install_security_headers(app)
    with TestClient(app) as client:
        response = client.get("/")

    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"


def test_security_middleware_preserves_explicit_route_header(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    app = FastAPI()

    @app.get("/")
    def root(response: Response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return {"ok": True}

    install_security_headers(app)
    with TestClient(app) as client:
        response = client.get("/")

    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["x-content-type-options"] == "nosniff"
