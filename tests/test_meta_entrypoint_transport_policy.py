from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def test_meta_entrypoint_secret_bearing_clients_disable_redirects() -> None:
    # OAuth exchange, ad-account discovery, account probe and campaign discovery.
    assert SOURCE.count("AsyncClient(timeout=20, follow_redirects=False)") >= 4


def test_meta_entrypoint_reuses_validated_graph_and_account_identifiers() -> None:
    assert "_validated_meta_ad_account_id" in SOURCE
    assert "_validated_meta_graph_version" in SOURCE
    assert "graph_version = _safe_meta_graph_version()" in SOURCE
    assert "ad_account = _normalized_meta_ad_account_id" in SOURCE


def test_meta_entrypoint_never_forwards_raw_provider_error_message() -> None:
    assert 'error.get("message")' not in SOURCE
    assert "_meta_error_detail(response, \"Meta ad-account discovery\")" in SOURCE
    assert "_meta_error_detail(probe, \"Meta ad account lookup\")" in SOURCE
    assert "_meta_error_detail(campaigns_response, \"Meta campaign-list lookup\")" in SOURCE


def test_meta_oauth_response_must_have_access_token_before_persistence() -> None:
    assert 'if not token_data.get("access_token")' in SOURCE
    assert "Meta token exchange returned no access token" in SOURCE
    assert "_safe_meta_payload(response, \"Meta token exchange\")" in SOURCE


def test_meta_entrypoint_keeps_read_only_scope_and_no_execution_mutations() -> None:
    forbidden = (
        "ads_management",
        "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
        "VEZMORA_EXECUTION_ENABLED =",
        "daily_budget",
        "pause_campaign",
        "update_campaign",
    )
    for marker in forbidden:
        assert marker not in SOURCE
