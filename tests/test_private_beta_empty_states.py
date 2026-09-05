from __future__ import annotations

from pathlib import Path


APP_JS = Path("static/app.js")


def _source() -> str:
    return APP_JS.read_text(encoding="utf-8")


def test_dashboard_empty_state_tells_pilot_user_what_to_do_next() -> None:
    source = _source()
    assert "Lägg till eller synka KPI-data." in source
    assert "Ingen KPI-data ännu." in source


def test_connector_empty_state_is_actionable_without_exposing_secrets() -> None:
    source = _source()
    assert "Needs setup" in source
    assert "Ready to connect" in source
    assert "Missing:" in source
    assert "OAuth credentials detected." in source

    forbidden = (
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_CLIENT_SECRET",
        "META_APP_SECRET",
        "STRIPE_SECRET_KEY",
        "CRON_SECRET",
    )
    for name in forbidden:
        assert name not in source


def test_onboarding_validation_keeps_required_fields_explicit() -> None:
    source = _source()
    assert "Fyll i företagsnamn, bransch och erbjudande." in source
    assert "Beskriv målgruppen innan du fortsätter." in source
    assert "Fyll i alla obligatoriska företagsfält." in source


def test_private_beta_ui_keeps_external_execution_visibly_guarded() -> None:
    source = _source()
    assert "External execution" in source
    assert "Autopilot worker execution" in source
    assert "BLOCKED IN BETA" in source
    assert "LOCKED" in source
