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
