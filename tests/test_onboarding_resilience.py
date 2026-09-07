from fastapi.testclient import TestClient

from app import store
from app.main import app


def _register(client: TestClient, email: str) -> int:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "verysecure123",
            "workspace_name": "Vexmera Pilot",
        },
    )
    assert response.status_code == 200
    return response.json()["workspace_id"]


def _profile(*, timezone: str = "Europe/Stockholm") -> dict[str, object]:
    return {
        "company_name": "Pilot Bakery",
        "industry": "Bakery",
        "market": "Sweden",
        "website": "https://example.com",
        "audience": "Local customers",
        "offer": "Fresh bread and pastries",
        "brand_voice": "warm and clear",
        "language": "sv",
        "primary_goal": "sales",
        "monthly_budget": 5000,
        "primary_channels": ["google"],
        "growth_target": "More qualified local demand",
        "biggest_marketing_problem": "Inconsistent acquisition",
        "timezone": timezone,
        "team_size": 2,
    }


def test_partial_onboarding_persists_without_marking_complete(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "onboarding-partial.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client, "partial-pilot@example.com")
        payload = _profile()
        payload["growth_target"] = "Reach more nearby customers"

        saved = client.put(
            f"/api/onboarding?workspace_id={workspace_id}",
            json=payload,
        )
        assert saved.status_code == 200
        assert saved.json()["completed"] is False

        restored = client.get(f"/api/onboarding?workspace_id={workspace_id}")
        assert restored.status_code == 200
        state = restored.json()
        assert state["completed"] is False
        assert state["data"]["company_name"] == "Pilot Bakery"
        assert state["data"]["growth_target"] == "Reach more nearby customers"
        assert state["data"]["primary_channels"] == ["google"]


def test_invalid_timezone_cannot_complete_onboarding(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "onboarding-timezone.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client, "timezone-pilot@example.com")

        response = client.post(
            f"/api/onboarding/complete?workspace_id={workspace_id}",
            json=_profile(timezone="Not/A_Real_Timezone"),
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Unknown timezone"

        state = client.get(f"/api/onboarding?workspace_id={workspace_id}").json()
        assert state["completed"] is False

        company = client.get(f"/api/company?workspace_id={workspace_id}")
        assert company.status_code == 200
        assert company.json() is None


def test_failed_completion_preserves_existing_partial_profile(tmp_path, monkeypatch):
    """A validation error must not erase the pilot user's already-entered answers."""
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "onboarding-preserve-partial.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client, "preserve-partial@example.com")
        partial = _profile()
        partial["growth_target"] = "Keep this answer after a failed submit"

        saved = client.put(f"/api/onboarding?workspace_id={workspace_id}", json=partial)
        assert saved.status_code == 200

        failed = client.post(
            f"/api/onboarding/complete?workspace_id={workspace_id}",
            json=_profile(timezone="Not/A_Real_Timezone"),
        )
        assert failed.status_code == 400

        restored = client.get(f"/api/onboarding?workspace_id={workspace_id}")
        assert restored.status_code == 200
        state = restored.json()
        assert state["completed"] is False
        assert state["data"]["company_name"] == "Pilot Bakery"
        assert state["data"]["growth_target"] == "Keep this answer after a failed submit"


def test_autosave_after_completion_does_not_reopen_onboarding(tmp_path, monkeypatch):
    """A late autosave must not send a completed pilot customer back into onboarding."""
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "onboarding-completed-autosave.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client, "completed-autosave@example.com")
        completed = client.post(
            f"/api/onboarding/complete?workspace_id={workspace_id}",
            json=_profile(),
        )
        assert completed.status_code == 200
        assert completed.json()["completed"] is True

        updated = _profile()
        updated["growth_target"] = "Updated after completion"
        autosave = client.put(f"/api/onboarding?workspace_id={workspace_id}", json=updated)
        assert autosave.status_code == 200

        restored = client.get(f"/api/onboarding?workspace_id={workspace_id}")
        assert restored.status_code == 200
        state = restored.json()
        assert state["completed"] is True
        assert state["completed_at"]
        assert state["data"]["growth_target"] == "Updated after completion"
