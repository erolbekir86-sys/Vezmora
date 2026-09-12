from pathlib import Path

from app.connector_empty_states import _with_empty_state_warning


ROOT = Path(__file__).resolve().parents[1]
STATE_UI = (ROOT / "static" / "connector-state-ui.js").read_text(encoding="utf-8")


def test_invalid_google_ads_response_is_not_reframed_as_healthy_empty_state() -> None:
    result = {
        "campaign_rows": 0,
        "ads_rows": 0,
        "warnings": ["Google Ads sync returned an invalid response"],
    }

    guarded = _with_empty_state_warning("Google Ads", result, 7)

    assert guarded["warnings"] == ["Google Ads sync returned an invalid response"]
    assert not any("connection can still be healthy" in warning for warning in guarded["warnings"])


def test_frontend_treats_missing_configuration_and_invalid_response_as_blocking() -> None:
    assert "text.includes('returned an invalid response')" in STATE_UI
    assert "text.includes(' is missing')" in STATE_UI
    assert "if (blockingWarning && rows === 0) return 'error'" in STATE_UI
    assert "if (rows > 0 && hasWarning) return 'data-warning'" in STATE_UI
    assert "text.includes('no campaign data found')" in STATE_UI
