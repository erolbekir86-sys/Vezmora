from fastapi.testclient import TestClient

from app import store
from app.main import app


def test_auth_workspace_profile_kpi_and_competitor(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "vezmora-test.db")
    store.init_db()
    with TestClient(app) as client:
        reg = client.post("/api/auth/register", json={
            "email": "founder@example.com",
            "password": "verysecure123",
            "workspace_name": "Vexmera Lab",
        })
        assert reg.status_code == 200
        workspace_id = reg.json()["workspace_id"]

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["workspaces"][0]["name"] == "Vexmera Lab"

        profile = {
            "name": "Nordic Peak",
            "industry": "Outdoor retail",
            "market": "Sweden",
            "website": "https://example.com",
            "audience": "Adults in Sweden",
            "offer": "Premium outdoor equipment",
            "brand_voice": "clear and premium",
            "language": "sv",
        }
        saved = client.put(f"/api/company?workspace_id={workspace_id}", json=profile)
        assert saved.status_code == 200
        loaded = client.get(f"/api/company?workspace_id={workspace_id}")
        assert loaded.json()["name"] == "Nordic Peak"

        kpi = client.post(f"/api/kpis?workspace_id={workspace_id}", json={
            "date": "2026-08-24",
            "impressions": 10000,
            "clicks": 500,
            "leads": 40,
            "conversions": 20,
            "spend_sek": 2000,
            "revenue_sek": 10000,
            "source": "manual",
        })
        assert kpi.status_code == 200
        dash = client.get(f"/api/dashboard?workspace_id={workspace_id}").json()
        assert dash["roas"] == 5
        assert dash["ctr"] == 5

        rival = client.post(f"/api/competitors?workspace_id={workspace_id}", json={
            "name": "Trail Rival",
            "url": "https://rival.example",
            "notes": "Watch offers and pricing",
        })
        assert rival.status_code == 200
        rivals = client.get(f"/api/competitors?workspace_id={workspace_id}").json()
        assert rivals[0]["name"] == "Trail Rival"
