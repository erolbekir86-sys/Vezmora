from __future__ import annotations

from app.public_health import _public_runtime_payload


def test_public_runtime_payload_has_a_strict_allowlist(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "abc123")
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret.invalid/db")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "secret-stripe")
    monkeypatch.setenv("SMTP_PASSWORD", "secret-smtp")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret-google")
    monkeypatch.setenv("META_APP_SECRET", "secret-meta")

    payload = _public_runtime_payload()

    assert set(payload) == {
        "ok",
        "service",
        "version",
        "platform",
        "environment",
        "deployment_revision",
    }
