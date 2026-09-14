from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from app.security_headers import install_security_headers


def _app(monkeypatch) -> FastAPI:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    app = FastAPI()

    @app.get("/api/private")
    def private_api():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/app")
    def product():
        return {"ok": True}

    @app.get("/public")
    def public():
        return {"ok": True}

    @app.get("/api/custom-robots")
    def custom_robots(response: Response):
        response.headers["X-Robots-Tag"] = "noindex"
        return {"ok": True}

    install_security_headers(app)
    return app


def test_private_surfaces_are_not_indexable(monkeypatch) -> None:
    with TestClient(_app(monkeypatch)) as client:
        api_response = client.get("/api/private")
        health_response = client.get("/health")
        app_response = client.get("/app")
        reset_response = client.get("/public?reset=one-time-secret")
        invite_response = client.get("/public?invite=one-time-secret")
        billing_response = client.get("/public?session_id=cs_test_private_session")
        public_response = client.get("/public")

    expected = "noindex, nofollow, noarchive"
    assert api_response.headers["x-robots-tag"] == expected
    assert health_response.headers["x-robots-tag"] == expected
    assert app_response.headers["x-robots-tag"] == expected
    assert reset_response.headers["x-robots-tag"] == expected
    assert invite_response.headers["x-robots-tag"] == expected
    assert billing_response.headers["x-robots-tag"] == expected
    assert "x-robots-tag" not in public_response.headers


def test_private_surface_noindex_preserves_explicit_route_policy(monkeypatch) -> None:
    with TestClient(_app(monkeypatch)) as client:
        response = client.get("/api/custom-robots")

    assert response.headers["x-robots-tag"] == "noindex"
