from app.connector_empty_states import _with_empty_state_warning


def test_zero_row_sync_gets_actionable_non_failure_warning():
    result = {"campaign_rows": 0, "ads_rows": 0, "warnings": []}

    guarded = _with_empty_state_warning("Google Ads", result, 30)

    assert guarded is result
    assert len(guarded["warnings"]) == 1
    warning = guarded["warnings"][0]
    assert "No campaign data found" in warning
    assert "30-day period" in warning
    assert "connection can still be healthy" in warning


def test_non_empty_sync_does_not_get_empty_state_warning():
    result = {"campaign_rows": 4, "ads_rows": 2, "warnings": []}

    guarded = _with_empty_state_warning("Meta Ads", result, 7)

    assert guarded["warnings"] == []


def test_empty_state_warning_is_idempotent():
    result = {"campaign_rows": 0, "warnings": []}

    _with_empty_state_warning("Meta Ads", result, 90)
    _with_empty_state_warning("Meta Ads", result, 90)

    assert len(result["warnings"]) == 1
