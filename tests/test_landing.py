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


def test_public_root_serves_marketing_site_and_points_ctas_to_app():
    with TestClient(app) as client:
        response = client.get('/')

    assert response.status_code == 200
    assert 'Förstå din marknadsföring.' in response.text
    assert 'id="authScreen"' not in response.text
    assert 'href="/app"' in response.text
    assert '<link rel="canonical" href="https://vexmera.com/" />' in response.text
    assert '<meta name="robots" content="index,follow" />' in response.text


def test_authenticated_product_shell_lives_under_app_and_is_noindex():
    with TestClient(app) as client:
        response = client.get('/app')
        slash = client.get('/app/')

    assert response.status_code == 200
    assert slash.status_code == 200
    assert 'id="authScreen"' in response.text
    assert '/static/app.js' in response.text
    assert '<meta name="robots" content="noindex,nofollow" />' in response.text
    assert response.headers['x-robots-tag'] == 'noindex, nofollow'
    assert 'Förstå din marknadsföring.' not in response.text


def test_legacy_product_return_links_are_forwarded_to_app():
    with TestClient(app, follow_redirects=False) as client:
        reset = client.get('/?reset=abc123')
        invite = client.get('/?invite=invite123')
        billing = client.get('/?billing=success&session_id=cs_test_123')

    assert reset.status_code == 302
    assert reset.headers['location'] == '/app?reset=abc123'
    assert invite.status_code == 302
    assert invite.headers['location'] == '/app?invite=invite123'
    assert billing.status_code == 302
    assert billing.headers['location'] == '/app?billing=success&session_id=cs_test_123'


def test_search_engine_files_publish_only_the_public_marketing_root():
    with TestClient(app) as client:
        robots = client.get('/robots.txt')
        sitemap = client.get('/sitemap.xml')

    assert robots.status_code == 200
    assert 'Disallow: /app' in robots.text
    assert 'Disallow: /api/' in robots.text
    assert 'Sitemap: https://vexmera.com/sitemap.xml' in robots.text

    assert sitemap.status_code == 200
    assert sitemap.headers['content-type'].startswith('application/xml')
    assert '<loc>https://vexmera.com/</loc>' in sitemap.text
    assert '<loc>https://vexmera.com/app</loc>' not in sitemap.text
