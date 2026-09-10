from app.connector_empty_states import _normalize_sync_result, _safe_period_days, _with_empty_state_warning


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


def test_ads_rows_prevent_false_empty_state_warning():
    result = {"campaign_rows": 0, "ads_rows": 3, "warnings": []}

    guarded = _with_empty_state_warning("Meta Ads", result, 7)

    assert guarded["warnings"] == []


def test_malformed_row_counts_are_treated_as_empty_safely():
    result = {"campaign_rows": "unknown", "ads_rows": None, "warnings": []}

    guarded = _with_empty_state_warning("Google Ads", result, 30)

    assert len(guarded["warnings"]) == 1


def test_empty_state_warning_is_idempotent():
    result = {"campaign_rows": 0, "warnings": []}

    _with_empty_state_warning("Meta Ads", result, 90)
    _with_empty_state_warning("Meta Ads", result, 90)

    assert len(result["warnings"]) == 1


def test_error_result_is_not_reframed_as_healthy_empty_state():
    result = {"error": "Provider unavailable", "status": 503}

    guarded = _with_empty_state_warning("Google Ads", result, 7)

    assert guarded is result
    assert "warnings" not in guarded


def test_http_error_status_is_not_reframed_as_healthy_empty_state():
    result = {"status": "429", "campaign_rows": 0, "ads_rows": 0}

    guarded = _with_empty_state_warning("Meta Ads", result, 7)

    assert "warnings" not in guarded


def test_explicit_ok_false_is_not_reframed_as_healthy_empty_state():
    result = {"ok": False, "campaign_rows": 0, "ads_rows": 0}

    guarded = _with_empty_state_warning("Google Ads", result, 7)

    assert "warnings" not in guarded


def test_explicit_success_false_is_not_reframed_as_healthy_empty_state():
    result = {"success": False, "campaign_rows": 0, "ads_rows": 0}

    guarded = _with_empty_state_warning("Meta Ads", result, 7)

    assert "warnings" not in guarded


def test_existing_scalar_provider_warning_is_preserved():
    result = {"campaign_rows": 0, "ads_rows": 0, "warnings": "Partial attribution data"}

    guarded = _with_empty_state_warning("Meta Ads", result, 30)

    assert guarded["warnings"][0] == "Partial attribution data"
    assert any("No campaign data found" in warning for warning in guarded["warnings"])


def test_google_ads_http_failure_warning_is_not_reframed_as_healthy_empty_state():
    result = {
        "campaign_rows": 0,
        "ads_rows": 0,
        "warnings": ["Google Ads sync failed (403)"],
    }

    guarded = _with_empty_state_warning("Google Ads", result, 7)

    assert guarded["warnings"] == ["Google Ads sync failed (403)"]
    assert not any("connection can still be healthy" in warning for warning in guarded["warnings"])


def test_google_ads_missing_configuration_is_not_reframed_as_healthy_empty_state():
    result = {
        "campaign_rows": 0,
        "ads_rows": 0,
        "warnings": ["GOOGLE_ADS_DEVELOPER_TOKEN is missing"],
    }

    guarded = _with_empty_state_warning("Google Ads", result, 7)

    assert guarded["warnings"] == ["GOOGLE_ADS_DEVELOPER_TOKEN is missing"]
    assert not any("connection can still be healthy" in warning for warning in guarded["warnings"])


def test_google_analytics_rows_get_metric_semantics_warning():
    result = {
        "analytics_rows": 4,
        "campaign_rows": 2,
        "ads_rows": 2,
        "warnings": [],
    }

    guarded = _with_empty_state_warning("Google Ads", result, 7)

    assert any("generic clicks KPI" in warning for warning in guarded["warnings"])
    assert any("sessions, not ad clicks" in warning for warning in guarded["warnings"])


def test_google_analytics_metric_semantics_warning_is_idempotent():
    result = {
        "analytics_rows": 1,
        "campaign_rows": 1,
        "ads_rows": 1,
        "warnings": [],
    }

    _with_empty_state_warning("Google Ads", result, 7)
    _with_empty_state_warning("Google Ads", result, 7)

    matching = [warning for warning in result["warnings"] if "generic clicks KPI" in warning]
    assert len(matching) == 1


def test_invalid_provider_result_becomes_safe_actionable_failure():
    guarded = _normalize_sync_result("Meta Ads", None)

    assert guarded["ok"] is False
    assert "invalid response" in str(guarded["error"])
    assert len(guarded["warnings"]) == 1
    assert "Retry the sync" in guarded["warnings"][0]
    assert "reconnect the provider" in guarded["warnings"][0]


def test_invalid_provider_result_is_not_reframed_as_empty_account():
    guarded = _normalize_sync_result("Google Ads", ["unexpected", "payload"])
    guarded = _with_empty_state_warning("Google Ads", guarded, 7)

    assert guarded["ok"] is False
    assert not any("connection can still be healthy" in warning for warning in guarded["warnings"])


def test_valid_provider_result_is_preserved_by_normalizer():
    result = {"campaign_rows": 2, "ads_rows": 1, "warnings": []}

    guarded = _normalize_sync_result("Google Ads", result)

    assert guarded is result


def test_empty_state_display_period_is_bounded_and_safe():
    assert _safe_period_days(0) == 1
    assert _safe_period_days(-30) == 1
    assert _safe_period_days(9999) == 365
    assert _safe_period_days("30") == 30
    assert _safe_period_days("invalid") == 7
    assert _safe_period_days(None) == 7


def test_empty_state_warning_never_displays_malformed_period():
    result = {"campaign_rows": 0, "ads_rows": 0, "warnings": []}

    guarded = _with_empty_state_warning("Meta Ads", result, -90)

    assert "selected 1-day period" in guarded["warnings"][0]
    assert "-90-day" not in guarded["warnings"][0]
