from __future__ import annotations

from fastapi.testclient import TestClient

from app import store
from app.main import app


EMAIL = "private-beta-smoke@example.com"
PASSWORD = "verysecure123"


def _onboarding_payload() -> dict[str, object]:
    return {
        "company_name": "Vexmera QA Test AB",
        "industry": "Software",
        "market": "Sweden",
        "website": "https://example.com",
        "audience": "Small businesses",
        "offer": "QA test service",
        "brand_voice": "clear, trustworthy, useful",
        "language": "sv",
        "primary_goal": "sales",
        "monthly_budget": 1000,
        "primary_channels": ["organic", "email"],
        "growth_target": "+10% test target",
        "biggest_marketing_problem": "Test-only QA workflow",
        "timezone": "Europe/Stockholm",
        "team_size": 1,
    }


def test_authenticated_private_beta_smoke(tmp_path, monkeypatch) -> None:
    """Cover the non-visual authenticated pilot journey in one session.

    Browser QA is still needed for layout/click evidence, but this test proves the
    core authenticated lifecycle without external providers or destructive actions:
    register, session, multi-workspace access, onboarding persistence, company
    context, privacy deletion preview, logout isolation and login recovery.
    """

    monkeypatch.setattr(store, "DB_PATH", tmp_path / "authenticated-private-beta-smoke.db")
    store.init_db()

    with TestClient(app) as client:
        register = client.post(
            "/api/auth/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "workspace_name": "Vexmera QA Test AB",
            },
        )
        assert register.status_code == 200
        first_workspace = register.json()["workspace_id"]

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == EMAIL

        second = client.post("/api/workspaces", json={"name": "Vexmera QA Secondary"})
        assert second.status_code == 200
        second_workspace = second.json()["id"]
        assert second_workspace != first_workspace

        workspaces = client.get("/api/workspaces")
        assert workspaces.status_code == 200
        visible_ids = {workspace["id"] for workspace in workspaces.json()}
        assert {first_workspace, second_workspace}.issubset(visible_ids)

        before = client.get(f"/api/onboarding?workspace_id={first_workspace}")
        assert before.status_code == 200
        assert before.json()["completed"] is False

        complete = client.post(
            f"/api/onboarding/complete?workspace_id={first_workspace}",
            json=_onboarding_payload(),
        )
        assert complete.status_code == 200
        assert complete.json()["completed"] is True

        after = client.get(f"/api/onboarding?workspace_id={first_workspace}")
        assert after.status_code == 200
        assert after.json()["completed"] is True

        company = client.get(f"/api/company?workspace_id={first_workspace}")
        assert company.status_code == 200
        assert company.json()["name"] == "Vexmera QA Test AB"
        assert company.json()["industry"] == "Software"
        assert company.json()["audience"] == "Small businesses"

        dashboard = client.get(f"/api/dashboard?workspace_id={first_workspace}")
        assert dashboard.status_code == 200

        billing = client.get(f"/api/billing?workspace_id={first_workspace}")
        assert billing.status_code == 200
        assert billing.json()["billing_status"] == "trialing"

        deletion_preview = client.get("/api/privacy/account-deletion-preview")
        assert deletion_preview.status_code == 200
        preview = deletion_preview.json()
        assert preview["requires_password_reauthentication"] is True
        assert preview["shared_workspace_memberships"] == 0
        assert {workspace["id"] for workspace in preview["owned_workspaces"]} == {
            first_workspace,
            second_workspace,
        }

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert client.get("/api/auth/me").status_code == 401
        assert client.get("/api/workspaces").status_code == 401
        assert client.get(f"/api/company?workspace_id={first_workspace}").status_code == 401

        login = client.post(
            "/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        assert login.status_code == 200
        assert client.get("/api/auth/me").status_code == 200

        recovered = client.get("/api/workspaces")
        assert recovered.status_code == 200
        assert {workspace["id"] for workspace in recovered.json()} == visible_ids

        persisted = client.get(f"/api/company?workspace_id={first_workspace}")
        assert persisted.status_code == 200
        assert persisted.json()["name"] == "Vexmera QA Test AB"
