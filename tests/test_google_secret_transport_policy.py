from pathlib import Path

import pytest

from app import google_read_reliability as reliability


ROOT = Path(__file__).resolve().parents[1]
READ_SOURCE = (ROOT / "app" / "google_read_reliability.py").read_text(encoding="utf-8")
DIAGNOSTIC_SOURCE = (ROOT / "app" / "google_ads_diagnostics.py").read_text(encoding="utf-8")
PRIVACY_SOURCE = (ROOT / "app" / "connector_privacy_controls.py").read_text(encoding="utf-8")


def test_google_secret_bearing_read_clients_disable_redirects() -> None:
    assert "AsyncClient(timeout=20, follow_redirects=False)" in READ_SOURCE
    assert "AsyncClient(timeout=30, follow_redirects=False)" in READ_SOURCE
    assert "AsyncClient(timeout=40, follow_redirects=False)" in READ_SOURCE
    assert "AsyncClient(timeout=20, follow_redirects=False)" in DIAGNOSTIC_SOURCE
    assert "AsyncClient(timeout=12, follow_redirects=False)" in PRIVACY_SOURCE


def test_ga_property_id_accepts_only_numeric_canonical_shapes() -> None:
    assert reliability._validated_ga_property_id("123456789") == "123456789"
    assert reliability._validated_ga_property_id("properties/123456789") == "123456789"
    assert reliability._validated_ga_property_id(123456789) == "123456789"
    assert reliability._validated_ga_property_id("") is None

    for value in (
        "properties/123/extra",
        "123?alt=evil",
        "https://example.test/123",
        "123#fragment",
        "properties/not-a-number",
    ):
        with pytest.raises(ValueError):
            reliability._validated_ga_property_id(value)


def test_google_ads_api_version_is_bounded_to_version_token() -> None:
    assert reliability._validated_google_ads_api_version("v25") == "v25"
    assert reliability._validated_google_ads_api_version("v19") == "v19"

    for value in ("25", "v25/other", "v25?x=1", "https://example.test/v25", "vX"):
        with pytest.raises(ValueError):
            reliability._validated_google_ads_api_version(value)


def test_policy_layer_contains_no_scope_or_execution_enablement() -> None:
    joined = "\n".join((READ_SOURCE, DIAGNOSTIC_SOURCE, PRIVACY_SOURCE))
    forbidden = (
        "GOOGLE_SCOPES =",
        "ads_management",
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "pause_campaign",
        "daily_budget",
    )
    for marker in forbidden:
        assert marker not in joined
