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


def test_synced_history_deletion_requires_explicit_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "history-confirm.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)
        response = client.delete(
            f"/api/privacy/synced-marketing-history?workspace_id={workspace_id}&confirm=NO"
        )
        assert response.status_code == 400
        assert "DELETE_SYNCED_HISTORY" in str(response.json()["detail"])


def test_synced_history_deletion_removes_provider_data_but_keeps_manual_kpis(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "history-delete.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)
        with store._connect() as con:
            con.execute(
                """INSERT INTO kpis
                   (workspace_id, metric_date, impressions, clicks, leads, conversions, spend_sek, revenue_sek, source, currency)
                   VALUES (?, '2026-09-01', 10, 2, 1, 1, 100, 300, 'manual', 'SEK')""",
                (workspace_id,),
            )
            con.execute(
                """INSERT INTO kpis
                   (workspace_id, metric_date, impressions, clicks, leads, conversions, spend_sek, revenue_sek, source, currency)
                   VALUES (?, '2026-09-01', 100, 20, 4, 3, 500, 1200, 'google_ads', 'SEK')""",
                (workspace_id,),
            )
            con.execute(
                """INSERT INTO campaign_metrics
                   (workspace_id, provider, external_campaign_id, campaign_name, metric_date, impressions, clicks, conversions, spend, revenue, currency)
                   VALUES (?, 'google_ads', 'campaign-1', 'Search', '2026-09-01', 100, 20, 3, 500, 1200, 'SEK')""",
                (workspace_id,),
            )
            con.execute(
                """INSERT INTO anomalies
                   (workspace_id, fingerprint, severity, title, body, metadata_json)
                   VALUES (?, 'fingerprint-1', 'medium', 'CPA changed', 'Example anomaly', '{}')""",
                (workspace_id,),
            )
            con.execute(
                """INSERT INTO notifications
                   (workspace_id, kind, title, body, metadata_json)
                   VALUES (?, 'anomaly', 'CPA changed', 'Example anomaly', '{}')""",
                (workspace_id,),
            )

        response = client.delete(
            f"/api/privacy/synced-marketing-history?workspace_id={workspace_id}&confirm=DELETE_SYNCED_HISTORY"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["deleted"] == {
            "campaign_metrics": 1,
            "synced_kpis": 1,
            "anomalies": 1,
            "anomaly_notifications": 1,
        }
        assert payload["manual_kpis_retained"] is True
        assert payload["connector_credentials_unchanged"] is True

        with store._connect() as con:
            campaign_count = con.execute(
                "SELECT COUNT(*) FROM campaign_metrics WHERE workspace_id=?", (workspace_id,)
            ).fetchone()[0]
            anomaly_count = con.execute(
                "SELECT COUNT(*) FROM anomalies WHERE workspace_id=?", (workspace_id,)
            ).fetchone()[0]
            synced_count = con.execute(
                "SELECT COUNT(*) FROM kpis WHERE workspace_id=? AND source='google_ads'", (workspace_id,)
            ).fetchone()[0]
            manual_count = con.execute(
                "SELECT COUNT(*) FROM kpis WHERE workspace_id=? AND source='manual'", (workspace_id,)
            ).fetchone()[0]
        assert campaign_count == 0
        assert anomaly_count == 0
        assert synced_count == 0
        assert manual_count == 1


def test_privacy_controls_require_owner_or_admin(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "history-role.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)
        with store._connect() as con:
            user_id = con.execute(
                "SELECT user_id FROM workspace_members WHERE workspace_id=?", (workspace_id,)
            ).fetchone()[0]
            con.execute(
                "UPDATE workspace_members SET role='viewer' WHERE workspace_id=? AND user_id=?",
                (workspace_id, user_id),
            )

        disconnect = client.post(f"/api/connectors/google/disconnect?workspace_id={workspace_id}")
        delete = client.delete(
            f"/api/privacy/synced-marketing-history?workspace_id={workspace_id}&confirm=DELETE_SYNCED_HISTORY"
        )
        assert disconnect.status_code == 403
        assert delete.status_code == 403
