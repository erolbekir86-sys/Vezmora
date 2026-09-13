from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
STATE_UI = (ROOT / "static" / "connector-state-ui.js").read_text(encoding="utf-8")


def test_product_shell_loads_connector_state_ui_after_existing_guards():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/connector-state-ui.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/app-accessibility-guard.js?build=" in page.text
    assert "/static/connector-state-ui.js?build=" in page.text
    assert page.text.index("/static/app-accessibility-guard.js?build=") < page.text.index(
        "/static/connector-state-ui.js?build="
    )


def test_connector_states_distinguish_unsynced_data_empty_warning_and_error():
    assert "return 'unsynced'" in STATE_UI
    assert "return 'error'" in STATE_UI
    assert "return 'data-warning'" in STATE_UI
    assert "return 'data'" in STATE_UI
    assert "return 'empty'" in STATE_UI
    assert "Ansluten · inte synkad" in STATE_UI
    assert "Data mottagen" in STATE_UI
    assert "Data mottagen · kontroll behövs" in STATE_UI
    assert "Ansluten · ingen kampanjdata" in STATE_UI
    assert "Synkfel" in STATE_UI


def test_blocking_provider_warnings_cannot_render_as_healthy_empty_state():
    assert "text.includes('sync failed')" in STATE_UI
    assert "text.includes('returned an invalid response')" in STATE_UI
    assert "text.includes(' is missing')" in STATE_UI
    assert "if (blockingWarning && rows === 0) return 'error'" in STATE_UI
    assert "if (rows > 0 && hasWarning) return 'data-warning'" in STATE_UI
    assert "text.includes('no campaign data found')" in STATE_UI


def test_empty_state_requires_explicit_empty_signal_or_row_telemetry():
    assert "const rowKeys = ['campaign_rows', 'ads_rows', 'analytics_rows']" in STATE_UI
    assert "Object.prototype.hasOwnProperty.call(lastSync, key)" in STATE_UI
    assert "if (explicitEmpty) return 'empty'" in STATE_UI
    assert "if (hasRowTelemetry && rows === 0) return 'empty'" in STATE_UI
    assert "if (explicitEmpty || rows === 0) return 'empty'" not in STATE_UI


def test_persistent_state_uses_saved_last_sync_metadata_read_only():
    assert "connection?.metadata?.last_sync" in STATE_UI
    assert "const data = await api(ws('/api/connectors'))" in STATE_UI
    assert "applyProviderState(provider, data[provider]?.connection)" in STATE_UI
    assert "window.loadConnectors = guardedLoadConnectors" in STATE_UI


def test_connector_state_copy_is_customer_safe_and_does_not_render_raw_warnings():
    assert "detail.textContent = copy.detail" in STATE_UI
    assert "warnings.map((value) => String(value).toLowerCase())" in STATE_UI
    assert "detail.textContent = warning" not in STATE_UI
    assert "innerHTML = warning" not in STATE_UI
    assert "Senaste synken kunde inte slutföras. Kontrollera anslutningen och försök igen." in STATE_UI
    assert "Anslutningen kan vara frisk." in STATE_UI


def test_connector_state_ui_has_no_provider_or_billing_mutations():
    forbidden = (
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
        "ads_management",
    )
    for marker in forbidden:
        assert marker not in STATE_UI
