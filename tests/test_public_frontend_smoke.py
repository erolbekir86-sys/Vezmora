from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import app


_STATIC_ASSET_RE = re.compile(r'(?:src|href)=["\'](/static/[^"\']+)["\']')


def _asset_path(url: str) -> str:
    return url.split('?', 1)[0]


def test_public_frontend_shells_and_local_assets_are_non_empty():
    """Catch deployments where HTML renders but a critical local asset is missing/empty.

    This intentionally stays network-free: it exercises the exact FastAPI routes and
    static files that Vercel packages from the repository without touching external
    ad providers, credentials, or mutable customer data.
    """
    with TestClient(app) as client:
        landing = client.get('/')
        product = client.get('/app')

        assert landing.status_code == 200
        assert product.status_code == 200
        assert len(landing.content) > 1_000
        assert len(product.content) > 1_000

        asset_urls = set(_STATIC_ASSET_RE.findall(landing.text))
        asset_urls.update(_STATIC_ASSET_RE.findall(product.text))

        # A blank-page regression is especially likely if the main JS/CSS shells
        # stop being referenced or stop being packaged. Keep these explicit gates.
        assert any('/static/landing.js' in url for url in asset_urls)
        assert any('/static/app.js' in url for url in asset_urls)
        assert any(url.endswith('.css') or '.css?' in url for url in asset_urls)

        for url in sorted(asset_urls):
            path = _asset_path(url)
            response = client.get(path)
            assert response.status_code == 200, f'missing local frontend asset: {path}'
            assert response.content, f'empty local frontend asset: {path}'
