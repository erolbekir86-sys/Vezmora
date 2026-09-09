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
