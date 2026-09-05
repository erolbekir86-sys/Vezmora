from __future__ import annotations

from fastapi.testclient import TestClient

from app import connector_privacy_controls, connectors, store
from app.main import app


def _register(client: TestClient) -> int:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "disconnect-test@example.com",
            "password": "verysecure123",
            "workspace_name": "Disconnect Test",
        },
    )
    assert response.status_code == 200
    return response.json()["workspace_id"]


def test_owner_can_disconnect_connector_and_local_secret_is_deleted(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "disconnect.db")
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "connector-disconnect-test-secret")
    store.init_db()

    async def fake_revoke(provider: str, secret_blob: str | None):
        assert provider == "google"
        assert secret_blob
        return True, True

    monkeypatch.setattr(connector_privacy_controls, "_revoke_provider_token", fake_revoke)

    with TestClient(app) as client:
        workspace_id = _register(client)
        secret_blob = connectors.encrypt_json(
            {"access_token": "test-access-token", "refresh_token": "test-refresh-token"}
        )
        store.save_connector(
            workspace_id=workspace_id,
            provider="google",
            status="connected",
            external_id="google-account-id",
            account_label="Google account",
            secret_blob=secret_blob,
            metadata={"analytics_property_id": "123456789", "ads_customer_id": "1112223334"},
        )

        response = client.post(f"/api/connectors/google/disconnect?workspace_id={workspace_id}")
        assert response.status_code == 200
        payload = response.json()
        assert payload == {
            "ok": True,
            "provider": "google",
            "connection_existed": True,
            "credentials_removed": True,
            "provider_revoke_attempted": True,
            "provider_revoke_succeeded": True,
            "historical_data_retained": True,
        }

        saved = store.get_connector(workspace_id, "google", include_secret=True)
        assert saved is not None
        assert saved["status"] == "disconnected"
        assert saved["secret_blob"] is None
        assert saved["external_id"] is None
        assert saved["account_label"] is None
        assert saved["metadata"]["historical_data_retained"] is True
        assert "analytics_property_id" not in saved["metadata"]
        assert "ads_customer_id" not in saved["metadata"]

        public = client.get(f"/api/connectors?workspace_id={workspace_id}").json()
        assert public["google"]["connection"]["status"] == "disconnected"
        assert "secret_blob" not in public["google"]["connection"]


def test_disconnect_is_idempotent_and_unknown_provider_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "disconnect-idempotent.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)

        response = client.post(f"/api/connectors/meta/disconnect?workspace_id={workspace_id}")
        assert response.status_code == 200
        assert response.json()["connection_existed"] is False
        assert response.json()["credentials_removed"] is True

        unknown = client.post(f"/api/connectors/tiktok/disconnect?workspace_id={workspace_id}")
        assert unknown.status_code == 404
