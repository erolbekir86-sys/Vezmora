from pathlib import Path

import pytest

from app import meta_read_reliability as reliability


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app" / "meta_read_reliability.py").read_text(encoding="utf-8")


def test_meta_read_client_explicitly_disables_redirects() -> None:
    assert "AsyncClient(timeout=40, follow_redirects=False)" in SOURCE
    assert "_validated_meta_paging_url" in SOURCE


def test_meta_ad_account_id_accepts_only_numeric_canonical_shapes() -> None:
    assert reliability._validated_meta_ad_account_id("123456") == "act_123456"
    assert reliability._validated_meta_ad_account_id("act_123456") == "act_123456"

    for value in (
        "",
        "act_",
        "act_123/insights",
        "123?access_token=synthetic",
        "https://evil.example/123",
        "act_123#fragment",
        "user@example.com",
    ):
        with pytest.raises(ValueError):
            reliability._validated_meta_ad_account_id(value)


def test_meta_graph_version_accepts_only_version_token() -> None:
    assert reliability._validated_meta_graph_version("v24.0") == "v24.0"
    assert reliability._validated_meta_graph_version("v25.1") == "v25.1"

    for value in ("24.0", "v24", "v24.0/other", "v24.0?x=1", "https://evil.example/v24.0"):
        with pytest.raises(ValueError):
            reliability._validated_meta_graph_version(value)


def test_meta_transport_policy_contains_no_execution_enablement() -> None:
    forbidden = (
        "ads_management",
        "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
        "VEZMORA_EXECUTION_ENABLED",
        "daily_budget",
        "pause_campaign",
    )
    for marker in forbidden:
        assert marker not in SOURCE
