from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import SESSION_COOKIE
from app.csrf_guard import install_csrf_guard


def _client() -> TestClient:
    app = FastAPI()

    @app.post("/api")
    def api_root_write() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/write")
    def api_write() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/read")
    def api_read() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/webhook")
    def webhook() -> dict[str, bool]:
        return {"ok": True}

    install_csrf_guard(app)
    return TestClient(app)


def test_cross_origin_authenticated_api_mutation_is_blocked():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-site authenticated request blocked"}
    assert "attacker.example" not in response.text


def test_cross_origin_authenticated_root_api_mutation_is_blocked():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-site authenticated request blocked"}


def test_fetch_metadata_blocks_cross_site_authenticated_mutation_without_origin():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Sec-Fetch-Site": "cross-site"},
    )

    assert response.status_code == 403


def test_same_origin_authenticated_api_mutation_is_allowed():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_cross_origin_request_without_session_cookie_is_not_treated_as_csrf():
    client = _client()

    response = client.post(
        "/api/write",
        headers={"Origin": "https://external-service.example"},
    )

    assert response.status_code == 200


def test_safe_methods_and_non_api_webhooks_are_unchanged():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")
    headers = {"Origin": "https://attacker.example", "Sec-Fetch-Site": "cross-site"}

    assert client.get("/api/read", headers=headers).status_code == 200
    assert client.post("/webhook", headers=headers).status_code == 200
