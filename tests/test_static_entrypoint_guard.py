from fastapi.testclient import TestClient

from app.main import app


def test_raw_product_html_redirects_to_canonical_app_route():
    with TestClient(app) as client:
        response = client.get("/static/index.html", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/app"
    assert response.headers["cache-control"].startswith("no-store")
    assert "<html" not in response.text.lower()


def test_raw_product_redirect_preserves_reset_invite_or_billing_query():
    with TestClient(app) as client:
        response = client.get(
            "/static/index.html?reset=opaque-test-token&billing=success",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "/app?reset=opaque-test-token&billing=success"


def test_raw_public_html_documents_redirect_to_canonical_public_routes():
    expected = {
        "/static/landing.html": "/",
        "/static/privacy.html": "/privacy",
        "/static/terms.html": "/terms",
    }
    with TestClient(app) as client:
        responses = {
            source: client.get(source, follow_redirects=False)
            for source in expected
        }

    for source, target in expected.items():
        assert responses[source].status_code == 302
        assert responses[source].headers["location"] == target


def test_normal_static_assets_are_not_redirected_or_blocked():
    with TestClient(app) as client:
        js = client.get("/static/app.js", follow_redirects=False)
        css = client.get("/static/app-modern.css", follow_redirects=False)

    assert js.status_code == 200
    assert css.status_code == 200
    assert "location" not in js.headers
    assert "location" not in css.headers


def test_guard_is_narrow_and_contains_no_account_or_provider_mutations():
    from app import static_entrypoint_guard as guard

    source = open(guard.__file__, encoding="utf-8").read()
    assert set(guard._RAW_STATIC_ENTRYPOINTS) == {
        "/static/index.html",
        "/static/landing.html",
        "/static/privacy.html",
        "/static/terms.html",
    }
    for forbidden in (
        "STRIPE_SECRET_KEY",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
        "method='POST'",
        "method=\"POST\"",
        "method='DELETE'",
        "method=\"DELETE\"",
        "autopilot/run-once",
        "billing/checkout",
    ):
        assert forbidden not in source
