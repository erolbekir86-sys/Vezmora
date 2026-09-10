from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.public_routing import PRODUCT_QUERY_KEYS


def test_connector_callback_return_query_is_forwarded_to_product_app() -> None:
    with TestClient(app, follow_redirects=False) as client:
        google = client.get("/?connected=google")
        meta = client.get("/?connected=meta")

    assert google.status_code == 302
    assert google.headers["location"] == "/app?connected=google"
    assert meta.status_code == 302
    assert meta.headers["location"] == "/app?connected=meta"


def test_billing_portal_view_return_is_forwarded_to_product_app() -> None:
    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/?view=team")

    assert response.status_code == 302
    assert response.headers["location"] == "/app?view=team"


def test_app_return_keys_keep_existing_capability_and_checkout_routes() -> None:
    assert {"reset", "invite", "billing", "connected", "view"}.issubset(PRODUCT_QUERY_KEYS)
