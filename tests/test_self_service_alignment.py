from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT = (ROOT / "static" / "self-service-alignment.js").read_text(encoding="utf-8")


def test_product_shell_loads_self_service_alignment_after_app_bundle():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/self-service-alignment.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/app.js?build=" in page.text
    assert "/static/self-service-alignment.js?build=" in page.text
    assert page.text.index("/static/app.js?build=") < page.text.index("/static/self-service-alignment.js?build=")


def test_in_app_plan_cards_align_with_public_start_growth_pro_model():
    assert "{key: 'start', label: 'Start', price: '995 kr'" in ALIGNMENT
    assert "{key: 'growth', label: 'Growth', price: '1 495 kr'" in ALIGNMENT
    assert "{key: 'pro', label: 'Pro', price: '2 995 kr'" in ALIGNMENT
    assert "button.dataset.plan = plan.key" in ALIGNMENT
    assert "Starter" not in ALIGNMENT
    assert "Scale" not in ALIGNMENT
    assert "1 499 kr" not in ALIGNMENT
    assert "5 999 kr" not in ALIGNMENT


def test_checkout_buttons_fail_closed_until_billing_explicitly_reports_ready():
    assert "setCheckoutAvailability(false)" in ALIGNMENT
    assert "billing?.checkout_ready === true" in ALIGNMENT
    assert "button.disabled = ready !== true" in ALIGNMENT
    assert "button.dataset.checkoutReady = ready === true ? 'true' : 'false'" in ALIGNMENT
    assert "Betalning öppnas när den verifierade Stripe-miljön är redo." in ALIGNMENT


def test_checkout_guard_wraps_team_loading_without_rebinding_checkout_handler():
    assert "const originalLoadTeam = typeof window.loadTeam === 'function' ? window.loadTeam : null" in ALIGNMENT
    assert "await originalLoadTeam.apply(this, args)" in ALIGNMENT
    assert "const billing = await api(ws('/api/billing'))" in ALIGNMENT
    assert "window.loadTeam = guardedLoadTeam" in ALIGNMENT
    assert "addEventListener('click'" not in ALIGNMENT


def test_runtime_status_uses_minimal_public_health_without_inferring_missing_secrets():
    assert "const payload = await api('/health')" in ALIGNMENT
    assert "payload?.ok === true" in ALIGNMENT
    assert "status.textContent = `System online${version}`" in ALIGNMENT
    assert "Systemstatus kunde inte verifieras." in ALIGNMENT
    assert "api_key_configured" not in ALIGNMENT
    assert "API-nyckel saknas" not in ALIGNMENT
    assert "window.loadSystemStatus = guardedLoadSystemStatus" in ALIGNMENT


def test_connector_sync_feedback_replaces_raw_json_with_provider_summaries():
    assert "providerSyncSummary('Google', payload.google)" in ALIGNMENT
    assert "providerSyncSummary('Meta', payload.meta)" in ALIGNMENT
    assert "showCustomerSyncMessage(summarizeConnectorSync(result))" in ALIGNMENT
    assert "alert(JSON.stringify" not in ALIGNMENT
    assert "synken kunde inte slutföras" in ALIGNMENT
    assert "Kontrollera anslutningsinställningarna eftersom synken gav en varning" in ALIGNMENT


def test_individual_connector_sync_buttons_use_safe_feedback_and_refresh_state():
    assert "document.querySelectorAll('#connectorGrid [data-sync]')" in ALIGNMENT
    assert "button.onclick = () => runIndividualConnectorSync(button)" in ALIGNMENT
    assert "await api(ws(`/api/connectors/${provider}/sync`)" in ALIGNMENT
    assert "showCustomerSyncMessage(providerSyncSummary(connectorProviderLabel(provider), result))" in ALIGNMENT
    assert "await window.loadConnectors()" in ALIGNMENT
    assert "window.loadConnectors = guardedLoadConnectors" in ALIGNMENT


def test_connector_sync_feedback_does_not_surface_raw_provider_exception_text():
    assert "${err.message}" not in ALIGNMENT
    assert ".textContent = err.message" not in ALIGNMENT
    assert "Synkningen kunde inte slutföras. Kontrollera anslutningarna och försök igen." in ALIGNMENT
    assert "Kontrollera anslutningen och försök igen." in ALIGNMENT


def test_completed_onboarding_routes_to_connections_and_preserves_read_only_beta_message():
    assert "activateView('connect')" in ALIGNMENT
    assert "await loadConnectors()" in ALIGNMENT
    assert "Koppla nu en datakälla" in ALIGNMENT
    assert "utan att ändra kampanjer, budgetar eller bud automatiskt" in ALIGNMENT
    assert "Steg ${onboardingStep} av 3" in ALIGNMENT


def test_alignment_layer_does_not_enable_sensitive_execution_or_modify_secrets():
    forbidden = (
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
        "STRIPE_SECRET_KEY",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
        "ads_management",
    )
    for marker in forbidden:
        assert marker not in ALIGNMENT
