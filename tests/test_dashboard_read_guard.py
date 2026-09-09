from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
GUARD = (ROOT / "static" / "dashboard-read-guard.js").read_text(encoding="utf-8")


def test_product_shell_loads_dashboard_read_guard_after_app_bundle():
    with TestClient(app) as client:
        page = client.get('/app')
        guard = client.get('/static/dashboard-read-guard.js')

    assert page.status_code == 200
    assert guard.status_code == 200
    assert '/static/app.js?build=' in page.text
    assert '/static/dashboard-read-guard.js?build=' in page.text
    assert page.text.index('/static/app.js?build=') < page.text.index('/static/dashboard-read-guard.js?build=')


def test_dashboard_read_failure_clears_potentially_stale_metrics():
    assert "value.includes('/api/dashboard')" in GUARD
    assert "value.includes('/api/kpis?')" in GUARD
    assert "node.textContent = '—'" in GUARD
    assert 'Kunde inte hämta aktuell data. Försök uppdatera igen.' in GUARD
    assert 'Aktuell KPI-data kunde inte verifieras.' in GUARD


def test_dashboard_guard_only_targets_get_reads():
    assert "const method = String(options.method || 'GET').toUpperCase()" in GUARD
    assert "if (method !== 'GET') return false" in GUARD


def test_dashboard_guard_does_not_expose_raw_errors_or_touch_sensitive_actions():
    forbidden = (
        '${err.message}',
        '.textContent = err.message',
        'String(err)',
        'external_execution',
        'autopilot/run-once',
        'billing/checkout',
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'META_APP_SECRET',
        'OPENAI_API_KEY',
        "method: 'POST'",
        "method: 'DELETE'",
    )
    for marker in forbidden:
        assert marker not in GUARD
