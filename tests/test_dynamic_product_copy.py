from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
COPY = (ROOT / "static" / "dynamic-product-copy.js").read_text(encoding="utf-8")
LOADING = (ROOT / "static" / "view-loading-state.js").read_text(encoding="utf-8")


def test_dynamic_copy_asset_is_reachable_and_loaded_from_stable_guard_chain():
    with TestClient(app) as client:
        page = client.get("/app")
        asset = client.get("/static/dynamic-product-copy.js")

    assert page.status_code == 200
    assert asset.status_code == 200
    assert "/static/view-loading-state.js?build=" in page.text
    assert "loadGuardAsset('/static/dynamic-product-copy.js'" in LOADING
    assert "script.src = `${path}?build=${build}`" in LOADING


def test_connect_system_copy_is_localized_without_translating_customer_free_text():
    for source, target in (
        ("Connected", "Ansluten"),
        ("Ready to connect", "Redo att ansluta"),
        ("Needs setup", "Kräver konfiguration"),
        ("Connect", "Anslut"),
        ("Sync", "Synka"),
        ("Never synced", "Aldrig synkad"),
    ):
        assert f"['{source}', '{target}']" in COPY

    assert "OAuth-konfiguration hittad." in COPY
    assert "Saknas:" in COPY
    assert "Senast synkad:" in COPY
    assert "Synkperiod " in COPY
    assert "createTreeWalker" not in COPY
    assert "MutationObserver" not in COPY


def test_queue_dynamic_copy_is_swedish_and_execution_is_visually_locked():
    for target in ("Godkänn", "Avvisa", "Förhandsgranska", "väntar", "godkänd", "hög", "medel", "låg"):
        assert target in COPY

    assert "const execute = card.querySelector('[data-execute]')" in COPY
    assert "execute.disabled = true" in COPY
    assert "execute.onclick = null" in COPY
    assert "execute.setAttribute('aria-disabled', 'true')" in COPY
    assert "execute.dataset.vexmeraExecutionLocked = 'true'" in COPY
    assert "execute.textContent = 'Extern körning avstängd'" in COPY
    assert "Private beta är recommendation-only." in COPY


def test_dynamic_copy_reapplies_after_relevant_async_renders():
    assert "wrapLoader('loadConnectors', enhanceConnect)" in COPY
    assert "wrapLoader('loadApprovals', enhanceQueue)" in COPY
    assert "wrapLoader('loadCompetitors', enhanceRivals)" in COPY
    assert "wrapLoader('loadBrief', enhanceBrief)" in COPY
    assert "wrapLoader('loadAutopilot', enhanceAutopilot)" in COPY
    assert "const result = await original.apply(this, args)" in COPY
    assert "queueMicrotask(() =>" in COPY


def test_rival_brief_and_autopilot_system_copy_are_localized():
    assert "Inte skannad ännu" in COPY
    assert "Kontrollerad " in COPY
    assert "förändring upptäckt" in COPY
    assert " · stabil" in COPY
    assert "Schemaläggaren är aktiverad i den här miljön." in COPY
    assert "Manuell brief fungerar fortfarande." in COPY
    for target in (
        "Extern körning",
        "Autopilot-körning",
        "Autonoma högriskåtgärder",
        "AKTIVERAD",
        "LÅST",
        "BLOCKERAD I BETA",
        "Föreslå",
        "Assisterad",
        "Autonom",
    ):
        assert target in COPY


def test_dynamic_copy_guard_contains_no_provider_or_business_mutations():
    for forbidden in (
        "fetch(",
        "api(",
        "XMLHttpRequest",
        "/api/executions/",
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
    ):
        assert forbidden not in COPY
