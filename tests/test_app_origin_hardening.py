from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import beta_readiness
from app.auth import SESSION_COOKIE
from app.csrf_guard import install_csrf_guard


def _csrf_client() -> TestClient:
    app = FastAPI()

    @app.post("/api/write")
    def write() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/auth/login")
    def login() -> dict[str, bool]:
        return {"ok": True}

    install_csrf_guard(app)
    return TestClient(app)


def test_invalid_configured_app_url_cannot_restore_host_header_trust(monkeypatch):
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.com/app")
    client = _csrf_client()

    response = client.post(
        "/api/auth/login",
        headers={"Host": "attacker.example", "Origin": "https://attacker.example"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-origin authentication request blocked"}


def test_invalid_configured_app_url_blocks_authenticated_browser_origin(monkeypatch):
    monkeypatch.setenv("VEZMORA_APP_URL", "https://user:vault@vexmera.com")
    client = _csrf_client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Host": "vexmera.com", "Origin": "https://vexmera.com"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-origin authenticated request blocked"}


def test_production_readiness_rejects_https_url_that_is_not_plain_origin(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.com/app?next=private")
    monkeypatch.delenv("VEZMORA_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)

    snapshot = beta_readiness.beta_safety_snapshot()

    assert snapshot["transport"]["app_url_https"] is True
    assert snapshot["production_transport_safe"] is False
    assert "production_transport_safe" in snapshot["pilot_readiness"]["configuration_blockers"]
