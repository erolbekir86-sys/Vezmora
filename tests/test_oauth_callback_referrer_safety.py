from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security_headers import install_security_headers


def test_oauth_error_callbacks_never_emit_referrers(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    app = FastAPI()

    @app.get("/api/connectors/google/callback")
    def google_callback():
        return {"ok": True}

    @app.get("/api/connectors/meta/callback")
    def meta_callback():
        return {"ok": True}

    install_security_headers(app)

    with TestClient(app) as client:
        responses = [
            client.get(
                "/api/connectors/google/callback"
                "?error=access_denied&error_description=user+cancelled"
            ),
            client.get(
                "/api/connectors/meta/callback"
                "?error=access_denied&error_description=user+cancelled"
            ),
        ]

    for response in responses:
        assert response.status_code == 200
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"
        assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
