from fastapi.testclient import TestClient

from app.main import app


def test_framework_docs_remain_available_for_local_development(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    with TestClient(app) as client:
        docs = client.get("/docs", follow_redirects=False)
        schema = client.get("/openapi.json", follow_redirects=False)

    assert docs.status_code == 200
    assert schema.status_code == 200
    assert schema.json()["info"]["title"] == "Vexmera API"


def test_framework_docs_and_schema_are_hidden_on_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    protected = ("/docs", "/docs/", "/docs/oauth2-redirect", "/redoc", "/openapi.json")
    with TestClient(app) as client:
        responses = [client.get(path, follow_redirects=False) for path in protected]

    for response in responses:
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}
        assert response.headers["cache-control"].startswith("no-store")
        assert response.headers["x-robots-tag"] == "noindex, nofollow"


def test_framework_docs_do_not_leak_route_existence_through_other_methods_on_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    probes = (
        ("POST", "/openapi.json"),
        ("PUT", "/docs"),
        ("PATCH", "/redoc"),
        ("DELETE", "/docs/oauth2-redirect"),
        ("OPTIONS", "/openapi.json"),
    )
    with TestClient(app) as client:
        responses = [client.request(method, path, follow_redirects=False) for method, path in probes]

    for response in responses:
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}
        assert response.headers["cache-control"].startswith("no-store")
        assert response.headers["x-robots-tag"] == "noindex, nofollow"
        assert "allow" not in response.headers


def test_production_docs_guard_does_not_block_product_api_or_static_assets(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    with TestClient(app) as client:
        app_page = client.get("/app", follow_redirects=False)
        health = client.get("/health", follow_redirects=False)
        static_js = client.get("/static/app.js", follow_redirects=False)
        unauthenticated_api = client.get("/api/auth/me", follow_redirects=False)

    assert app_page.status_code == 200
    assert health.status_code == 200
    assert static_js.status_code == 200
    assert unauthenticated_api.status_code == 401


def test_docs_guard_is_read_surface_only_and_contains_no_sensitive_actions():
    from app import production_docs_guard as guard

    source = open(guard.__file__, encoding="utf-8").read()
    assert guard._PRODUCTION_DOC_PATHS == frozenset(
        {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}
    )
    for forbidden in (
        "STRIPE_SECRET_KEY",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
        "billing/checkout",
        "autopilot/run-once",
        "pause_campaign",
        "daily_budget",
        "os.environ[",
    ):
        assert forbidden not in source
