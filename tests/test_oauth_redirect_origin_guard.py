from __future__ import annotations

import os

from app.production_env_guards import apply_production_env_guards


def _clear(monkeypatch):
    for name in ("VERCEL", "VEZMORA_APP_URL", "GOOGLE_REDIRECT_URI", "META_REDIRECT_URI"):
        monkeypatch.delenv(name, raising=False)


def test_vercel_preserves_exact_canonical_oauth_callbacks(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example/")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://vexmera.example/api/connectors/google/callback")
    monkeypatch.setenv("META_REDIRECT_URI", "https://vexmera.example/api/connectors/meta/callback")

    apply_production_env_guards()

    assert os.getenv("GOOGLE_REDIRECT_URI") == "https://vexmera.example/api/connectors/google/callback"
    assert os.getenv("META_REDIRECT_URI") == "https://vexmera.example/api/connectors/meta/callback"


def test_vercel_removes_mismatched_or_insecure_oauth_callbacks(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://vexmera.example/api/connectors/google/callback")
    monkeypatch.setenv("META_REDIRECT_URI", "https://other.example/api/connectors/meta/callback")

    apply_production_env_guards()

    assert os.getenv("GOOGLE_REDIRECT_URI") is None
    assert os.getenv("META_REDIRECT_URI") is None


def test_vercel_removes_wrong_provider_callback_path(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://vexmera.example/api/connectors/meta/callback")
    monkeypatch.setenv("META_REDIRECT_URI", "https://vexmera.example/api/connectors/google/callback")

    apply_production_env_guards()

    assert os.getenv("GOOGLE_REDIRECT_URI") is None
    assert os.getenv("META_REDIRECT_URI") is None


def test_vercel_oauth_redirects_fail_closed_when_canonical_app_url_is_missing(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://vexmera.example/api/connectors/google/callback")
    monkeypatch.setenv("META_REDIRECT_URI", "https://vexmera.example/api/connectors/meta/callback")

    apply_production_env_guards()

    assert os.getenv("GOOGLE_REDIRECT_URI") is None
    assert os.getenv("META_REDIRECT_URI") is None


def test_local_development_does_not_rewrite_oauth_redirects(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VEZMORA_APP_URL", "http://localhost:8000")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/custom-google-callback")
    monkeypatch.setenv("META_REDIRECT_URI", "http://localhost:8000/custom-meta-callback")

    apply_production_env_guards()

    assert os.getenv("GOOGLE_REDIRECT_URI") == "http://localhost:8000/custom-google-callback"
    assert os.getenv("META_REDIRECT_URI") == "http://localhost:8000/custom-meta-callback"
