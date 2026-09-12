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

    @app.post("/api/auth/login")
    def login() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/auth/register")
    def register() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/auth/password-reset/request")
    def reset_request() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/auth/password-reset/confirm")
    def reset_confirm() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/billing/webhook")
    def billing_webhook() -> dict[str, bool]:
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
    assert response.json() == {"detail": "Cross-origin authenticated request blocked"}
    assert "attacker.example" not in response.text


def test_cross_origin_authenticated_root_api_mutation_is_blocked():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-origin authenticated request blocked"}


def test_fetch_metadata_blocks_cross_site_authenticated_mutation_without_origin():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Sec-Fetch-Site": "cross-site"},
    )

    assert response.status_code == 403


def test_fetch_metadata_blocks_same_site_cross_origin_authenticated_mutation():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Sec-Fetch-Site": "same-site"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-origin authenticated request blocked"}


def test_same_origin_authenticated_api_mutation_is_allowed():
    client = _client()
    client.cookies.set(SESSION_COOKIE, "session-token")

    response = client.post(
        "/api/write",
        headers={"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_cross_origin_public_auth_browser_mutations_are_blocked_without_session():
    client = _client()
    headers = {"Origin": "https://attacker.example", "Sec-Fetch-Site": "cross-site"}

    for path in (
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/password-reset/request",
        "/api/auth/password-reset/confirm",
    ):
        response = client.post(path, headers=headers)
        assert response.status_code == 403
        assert response.json() == {"detail": "Cross-origin authentication request blocked"}


def test_same_origin_public_auth_browser_mutation_is_allowed():
    client = _client()
    response = client.post(
        "/api/auth/login",
        headers={"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"},
    )
    assert response.status_code == 200


def test_non_browser_api_client_without_origin_metadata_can_use_public_auth():
    client = _client()
    assert client.post("/api/auth/login").status_code == 200
    assert client.post("/api/auth/password-reset/request").status_code == 200


def test_cross_origin_unrelated_request_without_session_cookie_is_not_treated_as_csrf():
    client = _client()

    response = client.post(
        "/api/write",
        headers={"Origin": "https://external-service.example"},
    )

    assert response.status_code == 200


def test_safe_methods_and_non_auth_webhooks_are_unchanged():
    client = _client()
    headers = {"Origin": "https://attacker.example", "Sec-Fetch-Site": "cross-site"}

    assert client.get("/api/read", headers=headers).status_code == 200
    assert client.post("/api/billing/webhook", headers=headers).status_code == 200
    assert client.post("/webhook", headers=headers).status_code == 200
