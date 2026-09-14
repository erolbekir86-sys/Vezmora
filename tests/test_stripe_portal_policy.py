from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app import store, stripe_billing
from app.pricing import CURRENT_PRICING_VERSION


def _workspace_with_customer(tmp_path, monkeypatch) -> int:
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "stripe-portal.db")
    store.init_db()
    _, workspace_id = store.create_user("portal-owner@example.com", "salt", "hash", "Portal policy")
    store.set_workspace_billing(workspace_id, customer_id="cus_test_portal")
    return workspace_id


def test_portal_fails_closed_without_explicit_reviewed_configuration(tmp_path, monkeypatch) -> None:
    workspace_id = _workspace_with_customer(tmp_path, monkeypatch)
    monkeypatch.setenv("STRIPE_BILLING_PORTAL_CONFIGURATION_ID", "   \t  ")

    with pytest.raises(Exception) as exc_info:
        stripe_billing.create_portal(workspace_id)

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 503
    assert "approved private beta portal configuration" in str(getattr(exc, "detail", "")).lower()


def test_portal_session_is_pinned_to_explicit_configuration(tmp_path, monkeypatch) -> None:
    workspace_id = _workspace_with_customer(tmp_path, monkeypatch)
    captured: dict[str, object] = {}

    class PortalSessions:
        def create(self, params):
            captured.update(params)
            return SimpleNamespace(url="https://billing.stripe.test/portal")

    class FakeStripeClient:
        def __init__(self, key, **kwargs):
            assert key == "test-only-placeholder"
            self.v1 = SimpleNamespace(
                billing_portal=SimpleNamespace(sessions=PortalSessions()),
            )

    monkeypatch.setitem(sys.modules, "stripe", SimpleNamespace(StripeClient=FakeStripeClient))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "test-only-placeholder")
    monkeypatch.setenv("STRIPE_BILLING_PORTAL_CONFIGURATION_ID", "bpc_test_private_beta")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VEZMORA_APP_URL", raising=False)

    result = stripe_billing.create_portal(workspace_id)

    assert result["url"] == "https://billing.stripe.test/portal"
    assert captured == {
        "customer": "cus_test_portal",
        "configuration": "bpc_test_private_beta",
        "return_url": "http://localhost:8000/?view=team",
    }


def test_existing_active_subscription_cannot_switch_plan_through_checkout(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "stripe-plan-switch.db")
    store.init_db()
    _, workspace_id = store.create_user("active-owner@example.com", "salt", "hash", "Active billing")
    store.set_workspace_billing(
        workspace_id,
        plan="start",
        customer_id="cus_test_active",
        subscription_id="sub_test_active",
        billing_status="active",
    )
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", CURRENT_PRICING_VERSION)
    monkeypatch.setattr(stripe_billing, "_stripe_client", lambda: SimpleNamespace())

    with pytest.raises(Exception) as exc_info:
        stripe_billing.create_checkout(workspace_id, "active-owner@example.com", "pro")

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 409
    assert "already has a stripe subscription" in str(getattr(exc, "detail", "")).lower()
