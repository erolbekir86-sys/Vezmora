from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from app.security_headers import install_security_headers


def _client() -> TestClient:
    app = FastAPI()

    @app.get('/api/connectors/google/callback')
    def google_callback() -> RedirectResponse:
        return RedirectResponse('/app?connected=google')

    @app.get('/api/connectors/meta/callback/')
    def meta_callback() -> RedirectResponse:
        return RedirectResponse('/app?connected=meta')

    @app.get('/public')
    def public() -> dict[str, bool]:
        return {'ok': True}

    install_security_headers(app)
    return TestClient(app, follow_redirects=False)


def test_google_oauth_callback_with_one_time_values_is_no_referrer() -> None:
    with _client() as client:
        response = client.get('/api/connectors/google/callback?code=oauth-code&state=oauth_state')

    assert response.status_code in {302, 307}
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert 'no-store' in response.headers['cache-control']


def test_meta_oauth_callback_slash_variant_is_no_referrer() -> None:
    with _client() as client:
        response = client.get('/api/connectors/meta/callback/?code=oauth-code&state=oauth_state')

    assert response.headers['referrer-policy'] == 'no-referrer'


def test_code_query_on_unrelated_public_route_keeps_default_policy() -> None:
    with _client() as client:
        response = client.get('/public?code=not-an-oauth-callback')

    assert response.status_code == 200
    assert response.headers['referrer-policy'] == 'strict-origin-when-cross-origin'
