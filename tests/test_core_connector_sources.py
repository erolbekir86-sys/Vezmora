from __future__ import annotations

import pytest

from app import core


def _stub_core_dependencies(monkeypatch, connectors):
    monkeypatch.setattr(core, "dashboard_summary", lambda workspace_id: {})
    monkeypatch.setattr(core, "list_anomalies", lambda workspace_id, limit: [])
    monkeypatch.setattr(core, "list_approvals", lambda workspace_id, status, limit: [])
    monkeypatch.setattr(core, "recent_competitor_changes", lambda workspace_id, limit: [])
    monkeypatch.setattr(core, "campaign_summary", lambda workspace_id, days: [])
    monkeypatch.setattr(core, "get_connectors", lambda workspace_id: connectors)
    monkeypatch.setattr(core, "get_onboarding_profile", lambda workspace_id: {"completed": True})
    monkeypatch.setattr(core, "get_autopilot_settings", lambda workspace_id: {})


@pytest.mark.parametrize("provider", ["google", "meta", "instagram", "shopify"])
def test_any_supported_connected_provider_counts_as_live_data(monkeypatch, provider):
    _stub_core_dependencies(monkeypatch, [{"provider": provider, "status": "connected"}])

    result = core.core_today(1)

    assert all(card.get("source") != "data" for card in result["cards"])
    assert result["headline"] == "No critical blockers detected"


def test_no_connected_provider_keeps_data_connection_prompt(monkeypatch):
    _stub_core_dependencies(monkeypatch, [])

    result = core.core_today(1)

    data_cards = [card for card in result["cards"] if card.get("source") == "data"]
    assert len(data_cards) == 1
    assert data_cards[0]["title"] == "Connect live marketing data"
