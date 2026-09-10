from __future__ import annotations

from app import public_health


PUBLIC_RUNTIME_KEYS = {
    "ok",
    "service",
    "version",
    "platform",
    "environment",
    "deployment_revision",
}


def test_public_runtime_payload_has_exact_minimal_allowlist(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "deadbeef")

    payload = public_health._public_runtime_payload()

    assert set(payload) == PUBLIC_RUNTIME_KEYS
    assert payload["platform"] == "vercel"
    assert payload["environment"] == "production"
    assert payload["deployment_revision"] == "deadbeef"


def test_public_runtime_payload_never_grows_into_configuration_inventory(monkeypatch):
    # Populate representative sensitive configuration variables. Public health
    # must not reflect either values or configured/not-configured booleans.
    representative = {
        "DATABASE_URL": "postgresql://private.invalid/db",
        "OPENAI_API_KEY": "not-a-real-key",
        "STRIPE_SECRET_KEY": "not-a-real-key",
        "SMTP_PASSWORD": "not-a-real-password",
        "GOOGLE_CLIENT_SECRET": "not-a-real-secret",
        "META_APP_SECRET": "not-a-real-secret",
        "CRON_SECRET": "not-a-real-secret",
        "VEZMORA_SECRET_KEY": "not-a-real-secret",
    }
    for name, value in representative.items():
        monkeypatch.setenv(name, value)

    rendered = repr(public_health._public_runtime_payload())

    for name, value in representative.items():
        assert name.lower() not in rendered.lower()
        assert value not in rendered


def test_public_health_guard_is_installed_on_product_app():
    from app.main import app

    assert getattr(app.state, "vexmera_public_health_guard_installed", False) is True
