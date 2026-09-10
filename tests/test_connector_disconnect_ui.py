from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
STATE_UI = (ROOT / "static" / "connector-state-ui.js").read_text(encoding="utf-8")
DISCONNECT_UI = (ROOT / "static" / "connector-disconnect-ui.js").read_text(encoding="utf-8")


def test_connector_state_layer_loads_isolated_disconnect_ui_with_build_id():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/connector-disconnect-ui.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/connector-state-ui.js?build=" in page.text
    assert "`/static/connector-disconnect-ui.js?build=${build}`" in STATE_UI
    assert "window.__VEXMERA_BUILD__" in STATE_UI


def test_disconnect_control_is_fail_closed_to_owner_and_admin_roles():
    assert "const me = await api('/api/auth/me')" in DISCONNECT_UI
    assert "const role = roles.get(Number(currentWorkspaceId))" in DISCONNECT_UI
    assert "role === 'owner' || role === 'admin'" in DISCONNECT_UI
    assert "if (!allowed || !connected)" in DISCONNECT_UI
    assert "Fail closed" in DISCONNECT_UI


def test_disconnect_requires_explicit_fail_closed_confirmation_and_preserves_history_copy():
    assert "if (typeof window.confirm !== 'function') return;" in DISCONNECT_UI
    assert "const confirmed = window.confirm(" in DISCONNECT_UI
    assert "if (!confirmed) return;" in DISCONNECT_UI
    assert "Tidigare synkad historik behålls" in DISCONNECT_UI
    assert "method: 'POST'" in DISCONNECT_UI
    assert "ws(`/api/connectors/${provider}/disconnect`)" in DISCONNECT_UI
    assert "Tidigare synkhistorik finns kvar i workspacet" in DISCONNECT_UI


def test_disconnect_ui_handles_provider_revocation_without_raw_error_text():
    assert "provider_revoke_attempted === true" in DISCONNECT_UI
    assert "provider_revoke_succeeded === false" in DISCONNECT_UI
    assert "leverantörens återkallning kunde inte bekräftas" in DISCONNECT_UI
    assert "err.message" not in DISCONNECT_UI
    assert "error.message" not in DISCONNECT_UI


def test_disconnect_ui_cannot_delete_history_or_change_marketing_execution():
    forbidden = (
        "/api/privacy/synced-marketing-history",
        "method: 'DELETE'",
        "method: 'PUT'",
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
        assert marker not in DISCONNECT_UI
