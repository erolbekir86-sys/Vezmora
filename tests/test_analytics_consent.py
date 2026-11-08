from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "static" / "index.html"
CONSENT_JS = ROOT / "static" / "analytics-consent.js"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_authenticated_app_does_not_embed_google_analytics_before_consent():
    html = _text(INDEX_HTML)
    assert "googletagmanager.com/gtag/js" not in html
    assert '<script src="/static/analytics-consent.js?v=1"></script>' in html
    assert html.index("analytics-consent.js") < html.index("/static/app.js")


def test_analytics_consent_defaults_all_optional_google_storage_to_denied():
    script = _text(CONSENT_JS)
    default_consent = "window.gtag('consent', 'default'"
    assert default_consent in script
    assert script.index(default_consent) < script.index("function loadAnalytics()")
    for setting in (
        "analytics_storage: 'denied'",
        "ad_storage: 'denied'",
        "ad_user_data: 'denied'",
        "ad_personalization: 'denied'",
    ):
        assert setting in script


def test_google_analytics_is_loaded_only_for_an_explicit_grant():
    script = _text(CONSENT_JS)
    assert "if (consent === 'granted') loadAnalytics();" in script
    assert "if (value === 'granted') loadAnalytics();" in script
    assert "script.dataset.vexmeraAnalytics = 'true';" in script
    assert "https://www.googletagmanager.com/gtag/js?id=" in script
    assert "allow_google_signals: false" in script
    assert "allow_ad_personalization_signals: false" in script


def test_consent_can_be_withdrawn_and_ga_cookies_are_cleared_best_effort():
    script = _text(CONSENT_JS)
    assert "function clearAnalyticsCookies()" in script
    assert "/^_ga(?:_|$)/" in script
    assert "disableAnalytics({clearCookies: true})" in script
    assert "Cookieinställningar" in script
    assert "window.vexmeraOpenCookieSettings" in script
    assert "anonymiserad användningsstatistik" not in script


def test_public_marketing_page_ships_cookie_settings_runtime():
    """A settings control must ship its runtime, not merely link to privacy."""
    from html.parser import HTMLParser
    from fastapi.testclient import TestClient
    from app.main import app

    class Controls(HTMLParser):
        scripts = []
        cookie_controls = []
        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == 'script' and attributes.get('src'):
                self.scripts.append(attributes['src'])
            if 'data-vexmera-cookie-settings' in attributes:
                self.cookie_controls.append(attributes)

    with TestClient(app) as client:
        response = client.get('/')
        parsed = Controls()
        parsed.feed(response.text)
        assert parsed.cookie_controls
        assert all(control.get('href') == '/privacy' for control in parsed.cookie_controls)
        runtime_paths = [src for src in parsed.scripts if src.split('?')[0] == '/static/analytics-consent.js']
        assert len(runtime_paths) == 1
        assert client.get(runtime_paths[0]).status_code == 200
        assert 'googletagmanager.com/gtag/js' not in response.text
