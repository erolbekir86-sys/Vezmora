from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import connector_config_hardening as hardening
from app import connectors
import app.main as app_main


def _set_valid_google(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://example.test/google/callback")


def _set_valid_meta(monkeypatch) -> None:
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_APP_SECRET", "app-secret")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.test/meta/callback")


def test_connector_readiness_rejects_whitespace_only_google_config(monkeypatch) -> None:
    _set_valid_google(monkeypatch)
    _set_valid_meta(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "   ")

    readiness = connectors.connector_readiness()

    assert readiness["google"]["configured"] is False
    assert readiness["meta"]["configured"] is True


def test_connector_readiness_rejects_whitespace_only_meta_config(monkeypatch) -> None:
    _set_valid_google(monkeypatch)
    _set_valid_meta(monkeypatch)
    monkeypatch.setenv("META_REDIRECT_URI", "\t  ")

    readiness = connectors.connector_readiness()

    assert readiness["google"]["configured"] is True
    assert readiness["meta"]["configured"] is False


def test_google_oauth_start_fails_before_state_creation_for_blank_config(monkeypatch) -> None:
    _set_valid_google(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "   ")

    with pytest.raises(HTTPException) as exc_info:
        connectors.google_authorization_url(1, 1)

    assert exc_info.value.status_code == 503
    assert "not configured" in str(exc_info.value.detail).lower()


def test_meta_oauth_start_fails_before_state_creation_for_blank_config(monkeypatch) -> None:
    _set_valid_meta(monkeypatch)
    monkeypatch.setenv("META_REDIRECT_URI", "   ")

    with pytest.raises(HTTPException) as exc_info:
        connectors.meta_authorization_url(1, 1)

    assert exc_info.value.status_code == 503
    assert "not configured" in str(exc_info.value.detail).lower()


def test_oauth_token_storage_rejects_whitespace_only_encryption_secret(monkeypatch) -> None:
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "   ")

    with pytest.raises(HTTPException) as exc_info:
        connectors.encrypt_json({"access_token": "test-only"})

    assert exc_info.value.status_code == 503
    assert "required" in str(exc_info.value.detail).lower()


def test_app_main_uses_hardened_bound_connector_functions() -> None:
    assert app_main.connector_readiness is hardening.connector_readiness_hardened
    assert app_main.google_authorization_url is hardening.google_authorization_url_hardened
    assert app_main.meta_authorization_url is hardening.meta_authorization_url_hardened
    assert app_main.google_callback is hardening.google_callback_hardened
    assert app_main.meta_callback is hardening.meta_callback_hardened
