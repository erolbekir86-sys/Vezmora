from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.production_token_response_guard import install_production_token_response_guard


ROOT = Path(__file__).resolve().parents[1]
INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
MAIN = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
SOURCE = (ROOT / "app" / "production_token_response_guard.py").read_text(encoding="utf-8")


def _app() -> FastAPI:
    app = FastAPI()

    @app.post("/api/team/invites")
    def invite():
        return {"id": 1, "delivery": "queued_smtp_not_configured", "invite_token": "raw-invite-secret"}

    @app.post("/api/auth/password-reset/request")
    def reset():
        return {"ok": True, "message": "generic", "dev_reset_token": "raw-reset-secret"}

    @app.get("/health")
    def health():
        return {"ok": True, "invite_token": "not-a-protected-route"}

    install_production_token_response_guard(app)
    return app


def test_vercel_scrubs_raw_invite_and_reset_tokens(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(_app()) as client:
        invite = client.post("/api/team/invites")
        reset = client.post("/api/auth/password-reset/request")

    assert invite.status_code == 200
    assert invite.json() == {"id": 1, "delivery": "queued_smtp_not_configured"}
    assert reset.status_code == 200
    assert reset.json() == {"ok": True, "message": "generic"}


def test_local_development_keeps_existing_dev_fallback(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    with TestClient(_app()) as client:
        invite = client.post("/api/team/invites")
        reset = client.post("/api/auth/password-reset/request")

    assert invite.json()["invite_token"] == "raw-invite-secret"
    assert reset.json()["dev_reset_token"] == "raw-reset-secret"


def test_unrelated_routes_are_not_scrubbed(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(_app()) as client:
        health = client.get("/health")
    assert health.json()["invite_token"] == "not-a-protected-route"


def test_guard_covers_existing_production_token_fields_and_is_installed():
    assert 'result["invite_token"] = raw' in MAIN
    assert 'result["dev_reset_token"] = raw' in MAIN
    assert '"/api/team/invites": frozenset({"invite_token"})' in SOURCE
    assert '"/api/auth/password-reset/request": frozenset({"dev_reset_token"})' in SOURCE
    assert "install_production_token_response_guard" in INIT


def test_guard_is_response_only_and_does_not_touch_token_generation_or_delivery():
    assert "route.dependant.call = wrapped" in SOURCE
    assert "safe.pop(field, None)" in SOURCE
    for forbidden in (
        "token_urlsafe",
        "hashlib",
        "queue_email",
        "run_email_once",
        "SMTP_PASSWORD",
        "GOOGLE_CLIENT_SECRET",
        "META_APP_SECRET",
        "STRIPE_SECRET_KEY",
    ):
        assert forbidden not in SOURCE
