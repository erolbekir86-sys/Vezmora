from __future__ import annotations

from pathlib import Path

from app import connectors


CONNECTORS_SOURCE = Path(connectors.__file__).read_text(encoding="utf-8")


def test_google_ads_connector_sync_stays_read_only():
    """Keep pilot data sync separate from the explicitly gated execution adapter.

    Google Ads uses the broad `adwords` OAuth scope even for reporting. The connector
    module must therefore remain a reporting-only boundary: campaign mutations belong
    in the execution adapter, which is protected by VEZMORA_EXECUTION_ENABLED.
    """
    assert "googleAds:searchStream" in CONNECTORS_SOURCE

    forbidden_mutation_markers = (
        "campaigns:mutate",
        "campaignBudgets:mutate",
        "adGroups:mutate",
        "adGroupAds:mutate",
        "customerClients:mutate",
        "googleAds:mutate",
    )
    for marker in forbidden_mutation_markers:
        assert marker not in CONNECTORS_SOURCE


def test_meta_connector_does_not_request_management_scope_by_default(monkeypatch):
    monkeypatch.delenv("VEZMORA_ENABLE_META_EXECUTION_SCOPE", raising=False)

    # META_SCOPES is intentionally constructed at import time. In the default test
    # environment it must expose insights access only; execution is a separate opt-in.
    assert "ads_read" in connectors.META_SCOPES
    assert "ads_management" not in connectors.META_SCOPES


def test_connector_readiness_describes_reporting_only_behavior():
    readiness = connectors.connector_readiness()

    assert "Read-only sync" in str(readiness["google"]["notes"])
    assert "Ads insights by default" in str(readiness["meta"]["notes"])
