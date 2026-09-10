from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
LOADING = (ROOT / "static" / "view-loading-state.js").read_text(encoding="utf-8")


def test_product_shell_loads_view_loading_guard_after_existing_ui_guards():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/view-loading-state.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/connector-state-ui.js?build=" in page.text
    assert "/static/view-loading-state.js?build=" in page.text
    assert page.text.index("/static/connector-state-ui.js?build=") < page.text.index(
        "/static/view-loading-state.js?build="
    )


def test_loading_guard_covers_primary_async_views():
    expected = {
        "loadDashboard": "dashboard",
        "loadCoreToday": "dashboard",
        "loadCompetitors": "rivals",
        "loadConnectors": "connect",
        "loadApprovals": "queue",
        "loadAutopilot": "autopilot",
        "loadBrief": "brief",
        "loadInsights": "insights",
        "loadTeam": "team",
    }
    for loader, view_id in expected.items():
        assert f"{loader}: '{view_id}'" in LOADING


def test_loading_guard_is_concurrency_safe_and_always_clears_busy_state():
    assert "const busyCounts = new Map()" in LOADING
    assert "(busyCounts.get(viewId) || 0) + 1" in LOADING
    assert "Math.max(0, (busyCounts.get(viewId) || 1) - 1)" in LOADING
    assert "if (next > 0)" in LOADING
    assert "view.setAttribute('aria-busy', 'true')" in LOADING
    assert "view.setAttribute('aria-busy', 'false')" in LOADING
    assert "finally {" in LOADING
    assert "endBusy(viewId)" in LOADING


def test_loading_status_is_accessible_and_customer_facing():
    assert "status.setAttribute('role', 'status')" in LOADING
    assert "status.setAttribute('aria-live', 'polite')" in LOADING
    assert "status.setAttribute('aria-atomic', 'true')" in LOADING
    assert "status.textContent = 'Uppdaterar…'" in LOADING
    assert "status.hidden = true" in LOADING


def test_loading_guard_has_no_network_or_business_mutations():
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
        assert forbidden not in LOADING
