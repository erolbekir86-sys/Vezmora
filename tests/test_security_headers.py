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


def test_api_responses_are_no_store_without_changing_public_cache_policy(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    app = FastAPI()

    @app.get("/api/private")
    def private_api():
        return {"secret_adjacent": "workspace-data"}

    @app.get("/public")
    def public_route():
        return {"ok": True}

    install_security_headers(app)
    with TestClient(app) as client:
        api_response = client.get("/api/private")
        public_response = client.get("/public")

    assert api_response.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert api_response.headers["pragma"] == "no-cache"
    assert api_response.headers["expires"] == "0"
    assert api_response.headers["cdn-cache-control"] == "no-store"
    assert api_response.headers["vercel-cdn-cache-control"] == "no-store"
    assert "cache-control" not in public_response.headers
    assert "cdn-cache-control" not in public_response.headers


def test_api_no_store_preserves_explicit_route_cache_control(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    app = FastAPI()

    @app.get("/api/custom")
    def custom(response: Response):
        response.headers["Cache-Control"] = "private, no-store"
        return {"ok": True}

    install_security_headers(app)
    with TestClient(app) as client:
        response = client.get("/api/custom")

    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["vercel-cdn-cache-control"] == "no-store"


def test_vexmera_auth_errors_are_no_store(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "api-cache.db")

    with TestClient(main_module.app) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers["cdn-cache-control"] == "no-store"
    assert response.headers["vercel-cdn-cache-control"] == "no-store"
