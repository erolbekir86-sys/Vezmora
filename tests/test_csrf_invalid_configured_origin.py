from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import SESSION_COOKIE
from app.csrf_guard import install_csrf_guard


def _client() -> TestClient:
    app = FastAPI()

    @app.post("/api/write")
    def write() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/auth/login")
    def login() -> dict[str, bool]:
        return {"ok": True}

    install_csrf_guard(app)
    return TestClient(app)


def test_malformed_configured_origin_cannot_restore_host_header_trust(monkeypatch):
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.com/app")
    client = _client()

    response = client.post(
        "/api/auth/login",
        headers={"Host": "attacker.example", "Origin": "https://attacker.example"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-origin authentication request blocked"}


def test_configured_origin_with_credentials_fails_closed_for_authenticated_mutation(monkeypatch):
    monkeypatch.setenv("VEZMORA_APP_URL", "https://user:vault@vexmera.com")
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Host": "vexmera.com", "Origin": "https://vexmera.com"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-origin authenticated request blocked"}
