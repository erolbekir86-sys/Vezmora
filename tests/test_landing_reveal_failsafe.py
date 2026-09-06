from fastapi.testclient import TestClient

from app.main import app


def test_marketing_page_reveal_effects_fail_open_safely():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="landing-reveal-failsafe"' in html
    assert '.reveal{opacity:1!important;transform:none!important;filter:none!important}' in html
    assert 'document.documentElement.classList.add("vexmera-reveal-js")' in html
    assert 'document.documentElement.classList.remove("vexmera-reveal-js")' in html
    assert 'html.vexmera-reveal-js .reveal:not(.in-view)' in html
