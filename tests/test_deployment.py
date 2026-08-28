from __future__ import annotations

import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import store
from app.main import app
from app import stripe_billing
import main as deployment_main


def test_cron_requires_secret(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cron.db")
    monkeypatch.setenv("CRON_SECRET", "cron-test-secret")
    store.init_db()
    with TestClient(app) as client:
        assert client.get("/api/internal/cron/maintenance").status_code == 401
        response = client.get(
            "/api/internal/cron/maintenance",
            headers={"Authorization": "Bearer cron-test-secret"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["jobs_processed"] == 0


def test_checkout_has_beta_trial_and_real_test_price(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "stripe.db")
    store.init_db()
    _, workspace_id = store.create_user("owner@example.com", "salt", "hash", "Stripe test")

    captured = {}

    class Sessions:
        def create(self, params):
            captured.update(params)
            return SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.test/session")

    class PortalSessions:
        def create(self, params):
            return SimpleNamespace(url="https://billing.stripe.test/portal")

    class FakeStripeClient:
        def __init__(self, key, **kwargs):
            self.v1 = SimpleNamespace(
                checkout=SimpleNamespace(sessions=Sessions()),
                billing_portal=SimpleNamespace(sessions=PortalSessions()),
            )

        def construct_event(self, payload, signature, secret):
            return {"id": "evt_test", "type": "noop", "data": {"object": {}}}

    monkeypatch.setitem(sys.modules, "stripe", SimpleNamespace(StripeClient=FakeStripeClient))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "test-only-placeholder")
    monkeypatch.setenv("STRIPE_PRICE_STARTER", "price_1U82XoKROcXIKEHsjhbAapsJ")
    monkeypatch.setenv("VEZMORA_TRIAL_DAYS", "14")

    result = stripe_billing.create_checkout(workspace_id, "owner@example.com", "starter")
    assert result["trial_days"] == 14
    assert captured["line_items"][0]["price"] == "price_1U82XoKROcXIKEHsjhbAapsJ"
    assert captured["subscription_data"]["trial_period_days"] == 14
    assert captured["mode"] == "subscription"
    assert captured["integration_identifier"].startswith("vezmora_beta_")
    assert len(captured["integration_identifier"].split("_")[-1]) == 8


def test_storage_backend_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    assert store.storage_backend() == "sqlite"
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://example.turso.invalid")
    assert store.storage_backend() == "turso"


def test_deployment_security_headers(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(deployment_main.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"


def test_runtime_exposes_safe_smtp_readiness(monkeypatch):
    values = {
        "SMTP_HOST": "smtp.example.test",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "test-only-placeholder",
        "SMTP_FROM": "sender@example.test",
        "SMTP_STARTTLS": "true",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    with TestClient(deployment_main.app) as client:
        payload = client.get("/health/runtime").json()

    assert payload["smtp_host_configured"] is True
    assert payload["smtp_port_configured"] is True
    assert payload["smtp_username_configured"] is True
    assert payload["smtp_password_configured"] is True
    assert payload["smtp_from_configured"] is True
    assert payload["smtp_starttls_configured"] is True
    assert payload["smtp_configured"] is True
    assert "smtp_connection_ok" not in payload
