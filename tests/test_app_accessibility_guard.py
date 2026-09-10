from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
GUARD = (ROOT / "static" / "app-accessibility-guard.js").read_text(encoding="utf-8")


def test_product_shell_loads_accessibility_guard_after_other_ui_guards():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/app-accessibility-guard.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/self-service-alignment.js?build=" in page.text
    assert "/static/app-accessibility-guard.js?build=" in page.text
    assert page.text.index("/static/self-service-alignment.js?build=") < page.text.index(
        "/static/app-accessibility-guard.js?build="
    )


def test_auth_tabs_expose_keyboard_and_aria_tab_semantics():
    assert "tabList.setAttribute('role', 'tablist')" in GUARD
    assert "tab.setAttribute('role', 'tab')" in GUARD
    assert "panel.setAttribute('role', 'tabpanel')" in GUARD
    assert "tab.setAttribute('aria-selected'" in GUARD
    assert "event.key === 'ArrowRight'" in GUARD
    assert "event.key === 'ArrowLeft'" in GUARD
    assert "event.key === 'Home'" in GUARD
    assert "event.key === 'End'" in GUARD


def test_onboarding_dialog_traps_focus_and_restores_previous_focus():
    assert "modal.setAttribute('aria-describedby', 'onboardingError')" in GUARD
    assert "event.key !== 'Tab'" in GUARD
    assert "last.focus()" in GUARD
    assert "first.focus()" in GUARD
    assert "previousFocus = document.activeElement" in GUARD
    assert "previousFocus.focus()" in GUARD


def test_onboarding_progress_is_exposed_to_assistive_technology():
    assert "progress.setAttribute('role', 'progressbar')" in GUARD
    assert "progress.setAttribute('aria-valuemin', '1')" in GUARD
    assert "progress.setAttribute('aria-valuemax', '3')" in GUARD
    assert "progress.setAttribute('aria-valuenow', match[1])" in GUARD


def test_dynamic_customer_statuses_use_live_regions():
    assert "node.setAttribute('role', 'alert')" in GUARD
    assert "node.setAttribute('aria-live', 'assertive')" in GUARD
    assert "node.setAttribute('role', 'status')" in GUARD
    assert "node.setAttribute('aria-live', 'polite')" in GUARD


def test_accessibility_guard_has_no_sensitive_or_external_execution_logic():
    forbidden = (
        "STRIPE_SECRET_KEY",
        "billing/checkout",
        "connectors/all/sync",
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
        "ads_management",
        "campaign_id",
        "daily_budget",
    )
    for marker in forbidden:
        assert marker not in GUARD
