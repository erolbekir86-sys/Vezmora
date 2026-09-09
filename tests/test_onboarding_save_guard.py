from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
GUARD = (ROOT / "static" / "onboarding-save-guard.js").read_text(encoding="utf-8")


def test_product_shell_loads_onboarding_save_guard_after_app_bundle():
    with TestClient(app) as client:
        page = client.get('/app')
        guard = client.get('/static/onboarding-save-guard.js')

    assert page.status_code == 200
    assert guard.status_code == 200
    assert '/static/app.js?build=' in page.text
    assert '/static/onboarding-save-guard.js?build=' in page.text
    assert page.text.index('/static/app.js?build=') < page.text.index('/static/onboarding-save-guard.js?build=')


def test_onboarding_step_only_advances_after_successful_save():
    save_call = "await api(ws('/api/onboarding')"
    advance = "onboardingStep = Math.min(3, onboardingStep + 1)"
    error_message = "Kunde inte spara steget:"

    assert save_call in GUARD
    assert advance in GUARD
    assert GUARD.index(save_call) < GUARD.index(advance)
    assert "catch (err)" in GUARD
    assert error_message in GUARD
    assert "next.disabled = true" in GUARD
    assert "next.disabled = false" in GUARD


def test_onboarding_guard_does_not_enable_execution_or_touch_sensitive_settings():
    forbidden = (
        'external_execution',
        'autopilot/run-once',
        'billing/checkout',
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'META_APP_SECRET',
        'OPENAI_API_KEY',
    )
    for marker in forbidden:
        assert marker not in GUARD
