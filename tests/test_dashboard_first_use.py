from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
GUIDE = (ROOT / "static" / "dashboard-first-use.js").read_text(encoding="utf-8")
LOADING = (ROOT / "static" / "view-loading-state.js").read_text(encoding="utf-8")


def test_dashboard_first_use_asset_is_reachable_and_loaded_after_view_guard():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/dashboard-first-use.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/view-loading-state.js?build=" in page.text
    assert "loadGuardAsset('/static/dashboard-first-use.js'" in LOADING
    assert "script.src = `${path}?build=${build}`" in LOADING
    assert "window.__VEXMERA_BUILD__" in LOADING


def test_dashboard_guide_only_renders_for_verified_empty_kpi_state():
    assert "rows.querySelector('.error-text')" in GUIDE
    assert "rows.textContent.includes('Ingen KPI-data ännu.')" in GUIDE
    assert "if (!kpiTableIsEmpty())" in GUIDE
    assert "removeGuide()" in GUIDE
    assert "document.getElementById(GUIDE_ID)" in GUIDE


def test_dashboard_guide_has_one_clear_connection_action():
    assert "Kom igång med riktig data" in GUIDE
    assert "Anslut en datakälla så kan Vexmera börja bygga din översikt." in GUIDE
    assert "Anslut datakälla" in GUIDE
    assert "window.activateView('connect')" in GUIDE
    assert "[data-view=\"connect\"]" in GUIDE


def test_dashboard_guide_rechecks_after_dashboard_refresh_and_initial_render():
    assert "const original = window.loadDashboard" in GUIDE
    assert "return await" not in GUIDE  # guide must run after the wrapped loader resolves
    assert "const result = await original.apply(this, args)" in GUIDE
    assert "renderGuide()" in GUIDE
    assert "queueMicrotask(renderGuide)" in GUIDE


def test_dashboard_guide_is_mobile_accessible_and_has_no_business_mutations():
    assert "min-height: 44px" in GUIDE
    assert "@media (max-width: 680px)" in GUIDE
    assert "guide.setAttribute('role', 'status')" in GUIDE
    for forbidden in (
        "fetch(",
        "api(",
        "XMLHttpRequest",
        "method: 'POST'",
        "method: 'PUT'",
        "method: 'DELETE'",
        "billing/checkout",
        "autopilot/run-once",
        "pause_campaign",
        "daily_budget",
        "STRIPE_SECRET_KEY",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
    ):
        assert forbidden not in GUIDE
