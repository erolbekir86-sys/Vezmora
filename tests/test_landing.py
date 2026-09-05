from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_marketing_landing_is_shipped_as_public_static_asset():
    with TestClient(app) as client:
        response = client.get('/static/landing.html')
        script = client.get('/static/landing.js')

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert script.status_code == 200
    html = response.text
    assert 'Vexmera — AI Marketing Officer' in html
    assert 'Kontroll före automation' in html
    assert '/static/landing.js' in html
    # The dashboard on the marketing page uses illustrative values. Keep a
    # visible demo marker in the shipped UI so example metrics cannot silently
    # turn into implied customer/live data during design iterations.
    assert 'DEMO DATA' in script.text


def test_marketing_landing_demo_window_matches_the_current_14_day_story():
    with TestClient(app) as client:
        html = client.get('/static/landing.html').text

    assert '<div class="dash-date">14 <span data-i18n="dash.days">dagar</span></div>' in html
    assert 'de senaste 14 dagarna' in html
    assert '<span>Dag 14</span>' in html
    assert '<span>Dag 30</span>' not in html


def test_marketing_landing_marks_ga4_as_current_private_beta_integration():
    with TestClient(app) as client:
        html = client.get('/static/landing.html').text

    ga4 = '<strong>GA4</strong><small data-i18n="integrations.connected">Privat beta</small>'
    assert ga4 in html
    assert '<strong>GA4</strong><small data-i18n="integrations.soon">Kommer snart</small>' not in html


def test_marketing_hero_has_a_desktop_layout_guard_against_copy_clipping():
    with TestClient(app) as client:
        html = client.get('/static/landing.html').text

    assert 'id="hero-layout-guard"' in html
    assert '.hero-copy{min-width:0!important;max-width:690px!important}' in html
    assert 'font-size:clamp(52px,4.8vw,72px)!important' in html
    assert 'overflow:visible!important' in html


def test_marketing_landing_does_not_expose_internal_execution_controls():
    with TestClient(app) as client:
        html = client.get('/static/landing.html').text

    forbidden = (
        'VEZMORA_EXECUTION_ENABLED',
        'VEZMORA_AUTOPILOT_EXECUTION_ENABLED',
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'META_APP_SECRET',
        'OPENAI_API_KEY',
        'ads_management',
    )
    for marker in forbidden:
        assert marker not in html


def test_existing_app_root_still_serves_authenticated_app_shell():
    with TestClient(app) as client:
        response = client.get('/')

    assert response.status_code == 200
    assert 'id="authScreen"' in response.text
    assert '/static/app.js' in response.text
    # Root remains the authenticated product shell, not the public landing.
    # Shared brand language is allowed, so use the landing hero itself as the
    # regression marker instead of banning a reusable eyebrow phrase.
    assert 'Förstå din marknadsföring.' not in response.text
