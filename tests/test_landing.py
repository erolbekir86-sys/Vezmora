from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_marketing_landing_is_shipped_as_public_static_asset():
    with TestClient(app) as client:
        response = client.get('/static/landing.html')

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    html = response.text
    assert 'Vexmera — AI Marketing Officer' in html
    assert 'Privat beta' in html
    assert 'Kontroll före automation' in html


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


def test_existing_app_root_is_not_replaced_by_marketing_page():
    with TestClient(app) as client:
        response = client.get('/')

    assert response.status_code == 200
    assert 'Vexmera — AI Marketing Officer' not in response.text
