from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


_STATIC_ASSET_RE = re.compile(r'(?:src|href)=["\'](/static/[^"\']+)["\']')
_DYNAMIC_ASSET_RE = re.compile(r'/static/[A-Za-z0-9._/-]+\.(?:css|js)')
_ROOT = Path(__file__).resolve().parent.parent


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

        # The premium landing loader injects additional assets at runtime. Those
        # references do not appear in the server-rendered HTML, so include them in
        # the packaging smoke test explicitly to prevent a "200 but blank/broken"
        # deployment when a dynamically loaded file is missing.
        premium_loader = (_ROOT / 'static' / 'landing-premium.js').read_text(encoding='utf-8')
        asset_urls.update(_DYNAMIC_ASSET_RE.findall(premium_loader))

        # A blank-page regression is especially likely if the main JS/CSS shells
        # stop being referenced or stop being packaged. Keep these explicit gates.
        assert any('/static/landing.js' in url for url in asset_urls)
        assert any('/static/app.js' in url for url in asset_urls)
        assert '/static/landing-premium.js' in {_asset_path(url) for url in asset_urls}
        assert '/static/landing-conversion.js' in {_asset_path(url) for url in asset_urls}
        assert '/static/landing-ai-workflow.css' in {_asset_path(url) for url in asset_urls}
        assert any(url.endswith('.css') or '.css?' in url for url in asset_urls)

        for url in sorted(asset_urls):
            path = _asset_path(url)
            response = client.get(path)
            assert response.status_code == 200, f'missing local frontend asset: {path}'
            assert response.content, f'empty local frontend asset: {path}'
