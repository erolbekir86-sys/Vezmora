from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.oauth_callback_guard import (
    OAUTH_CODE_MAX_LENGTH,
    OAUTH_STATE_MAX_LENGTH,
    install_oauth_callback_guard,
)


ROOT = Path(__file__).resolve().parents[1]
CONNECTORS = (ROOT / "app" / "connectors.py").read_text(encoding="utf-8")
INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")


def _guarded_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/connectors/google/callback")
    def google_callback(code: str, state: str):
        return {"provider": "google", "code": code, "state": state}

    @app.get("/api/connectors/meta/callback")
    def meta_callback(code: str, state: str):
        return {"provider": "meta", "code": code, "state": state}

    @app.get("/health")
    def health():
        return {"ok": True}

    install_oauth_callback_guard(app)
    return app


def test_valid_google_and_meta_callbacks_pass_through():
    state = "Abc_123-safe-state"
    with TestClient(_guarded_app()) as client:
        google = client.get("/api/connectors/google/callback", params={"code": "normal-code", "state": state})
        meta = client.get("/api/connectors/meta/callback", params={"code": "normal-code", "state": state})

    assert google.status_code == 200
    assert google.json()["provider"] == "google"
    assert meta.status_code == 200
    assert meta.json()["provider"] == "meta"


def test_oversized_state_is_rejected_before_callback_handler():
    with TestClient(_guarded_app()) as client:
        response = client.get(
            "/api/connectors/google/callback",
            params={"code": "normal-code", "state": "a" * (OAUTH_STATE_MAX_LENGTH + 1)},
        )

    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == "Invalid OAuth state format"


def test_malformed_state_is_rejected_for_both_providers():
    for path in ("/api/connectors/google/callback", "/api/connectors/meta/callback"):
        with TestClient(_guarded_app()) as client:
            response = client.get(path, params={"code": "normal-code", "state": "bad state å"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid OAuth state format"


def test_oversized_authorization_code_is_rejected():
    with TestClient(_guarded_app()) as client:
        response = client.get(
            "/api/connectors/meta/callback",
            params={"code": "c" * (OAUTH_CODE_MAX_LENGTH + 1), "state": "valid_state-123"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid OAuth authorization code"


def test_missing_query_values_keep_fastapi_validation_contract():
    with TestClient(_guarded_app()) as client:
        missing_state = client.get("/api/connectors/google/callback", params={"code": "normal-code"})
        missing_code = client.get("/api/connectors/meta/callback", params={"state": "valid_state-123"})

    assert missing_state.status_code == 422
    assert missing_code.status_code == 422


def test_non_callback_routes_are_untouched():
    with TestClient(_guarded_app()) as client:
        response = client.get("/health", params={"state": "x" * 1000, "code": "y" * 5000})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_generated_oauth_state_format_fits_guard_and_guard_is_installed():
    assert "state = secrets.token_urlsafe(28)" in CONNECTORS
    assert OAUTH_STATE_MAX_LENGTH >= 64
    assert "install_oauth_callback_guard" in INIT


def test_guard_contains_no_provider_calls_or_secret_handling():
    source = (ROOT / "app" / "oauth_callback_guard.py").read_text(encoding="utf-8")
    for forbidden in (
        "httpx",
        "requests",
        "GOOGLE_CLIENT_SECRET",
        "META_APP_SECRET",
        "access_token",
        "client.post",
        "client.get",
        "save_connector",
        "consume_oauth_state",
    ):
        assert forbidden not in source
