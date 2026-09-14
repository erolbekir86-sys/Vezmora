from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parent.parent
CHECKOUT_INTENT = (ROOT / "static" / "checkout-intent.js").read_text(encoding="utf-8")


def test_public_pricing_ctas_preserve_monthly_plan_into_product_shell():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert 'href="/app?plan=start"' in response.text
    assert 'href="/app?plan=growth"' in response.text
    assert 'href="/app?plan=pro"' in response.text


def test_public_private_beta_does_not_offer_unimplemented_annual_checkout():
    with TestClient(app) as client:
        response = client.get("/")

    assert 'data-billing="yearly" type="button" disabled aria-disabled="true"' in response.text
    assert "Efter privat beta" in response.text
    assert "After private beta" in response.text


def test_legacy_root_plan_intent_is_forwarded_to_product_shell():
    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/?plan=pro")

    assert response.status_code == 302
    assert response.headers["location"] == "/app?plan=pro"


def test_product_shell_loads_checkout_intent_after_billing_alignment():
    with TestClient(app) as client:
        response = client.get("/app")

    assert response.status_code == 200
    alignment = response.text.index("/static/self-service-alignment.js?build=")
    checkout = response.text.index("/static/checkout-intent.js?build=")
    accessibility = response.text.index("/static/app-accessibility-guard.js?build=")
    assert alignment < checkout < accessibility


def test_checkout_intent_is_allowlisted_fail_closed_and_readiness_aware():
    assert "new Set(['start', 'growth', 'pro'])" in CHECKOUT_INTENT
    assert "if (!allowedPlans.has(requestedPlan))" in CHECKOUT_INTENT
    assert "typeof currentWorkspaceId === 'undefined' || !currentWorkspaceId" in CHECKOUT_INTENT
    assert "const billing = await api(ws('/api/billing'))" in CHECKOUT_INTENT
    assert "billing?.checkout_ready !== true" in CHECKOUT_INTENT
    assert "activateView('team')" in CHECKOUT_INTENT
    assert "await startCheckout(requestedPlan)" in CHECKOUT_INTENT
    assert "clean.delete('plan')" in CHECKOUT_INTENT
