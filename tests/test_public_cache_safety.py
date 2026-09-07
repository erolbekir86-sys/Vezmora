from fastapi.testclient import TestClient

from app.main import app


def test_public_html_shells_disable_browser_and_cdn_revalidation_cache():
    with TestClient(app) as client:
        marketing = client.get("/")
        product = client.get("/app")

    for response in (marketing, product):
        assert response.status_code == 200
        cache_control = response.headers.get("cache-control", "")
        assert "no-store" in cache_control
        assert "no-cache" in cache_control
        assert "must-revalidate" in cache_control
        assert response.headers.get("pragma") == "no-cache"
        assert response.headers.get("expires") == "0"
        assert response.headers.get("cdn-cache-control") == "no-store"
        assert response.headers.get("vercel-cdn-cache-control") == "no-store"
