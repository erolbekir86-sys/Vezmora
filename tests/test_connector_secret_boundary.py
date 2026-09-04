from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import store
from app.main import app


def _register(client: TestClient) -> int:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "connector-secret-test@example.com",
            "password": "verysecure123",
            "workspace_name": "Connector Secret Boundary",
        },
    )
    assert response.status_code == 200
    return response.json()["workspace_id"]


def test_connector_listing_never_exposes_secret_blob(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "connector-secrets.db")
    store.init_db()

    sentinel = "SENTINEL_OAUTH_TOKEN_MUST_NEVER_LEAK"

    with TestClient(app) as client:
        workspace_id = _register(client)
        store.save_connector(
            workspace_id=workspace_id,
            provider="google",
            status="connected",
            external_id="test-google-account",
            account_label="Google account",
            secret_blob=sentinel,
            metadata={"analytics_property_id": "123456789"},
        )

        response = client.get(f"/api/connectors?workspace_id={workspace_id}")
        assert response.status_code == 200

        payload = response.json()
        serialized = json.dumps(payload)

        assert sentinel not in serialized
        assert "secret_blob" not in serialized
        assert payload["google"]["connection"]["status"] == "connected"
        assert payload["google"]["connection"]["metadata"]["analytics_property_id"] == "123456789"
