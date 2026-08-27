from fastapi.testclient import TestClient

from app import store
from app.autopilot import evaluate_autopilot_policy
from app.main import app


def register(client: TestClient, email: str = "owner06@example.com") -> int:
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "verysecure123",
        "workspace_name": "Vexmera Private Beta",
    })
    assert res.status_code == 200
    return res.json()["workspace_id"]


def onboarding_payload():
    return {
        "company_name": "Northstar Coffee",
        "industry": "Coffee ecommerce",
        "market": "Sweden",
        "website": "https://example.com",
        "audience": "Urban coffee enthusiasts in Sweden",
        "offer": "Fresh specialty coffee delivered quickly",
        "brand_voice": "warm, expert, minimal",
        "language": "sv",
        "primary_goal": "sales",
        "monthly_budget": 25000,
        "primary_channels": ["meta", "google", "email"],
        "growth_target": "+20% revenue in six months",
        "biggest_marketing_problem": "Paid traffic is inconsistent",
        "timezone": "Europe/Stockholm",
        "team_size": 3,
    }


def test_onboarding_core_and_beta_feedback(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "v06.db")
    store.init_db()
    with TestClient(app) as client:
        workspace_id = register(client)
        state = client.get(f"/api/onboarding?workspace_id={workspace_id}").json()
        assert state["completed"] is False

        complete = client.post(f"/api/onboarding/complete?workspace_id={workspace_id}", json=onboarding_payload())
        assert complete.status_code == 200
        assert complete.json()["completed"] is True
        company = client.get(f"/api/company?workspace_id={workspace_id}").json()
        assert company["name"] == "Northstar Coffee"

        today = client.get(f"/api/core/today?workspace_id={workspace_id}")
        assert today.status_code == 200
        assert today.json()["onboarding_complete"] is True
        assert today.json()["cards"]

        feedback = client.post(f"/api/beta/feedback?workspace_id={workspace_id}", json={
            "score": 5, "category": "core", "message": "Useful priorities"
        })
        assert feedback.status_code == 200


def test_autopilot_policy_is_guarded(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "autopilot06.db")
    store.init_db()
    with TestClient(app) as client:
        workspace_id = register(client, "auto06@example.com")
        saved = client.put(f"/api/autopilot?workspace_id={workspace_id}", json={
            "mode": "autopilot",
            "daily_spend_cap": 1000,
            "max_budget_change_pct": 10,
            "allowed_actions": ["google.set_daily_budget", "google.pause_campaign"],
        })
        assert saved.status_code == 200

        low = client.post(f"/api/approvals?workspace_id={workspace_id}", json={
            "action_type": "google.set_daily_budget",
            "title": "Small budget increase",
            "description": "Increase daily budget inside guardrails",
            "provider": "google",
            "risk_level": "medium",
            "payload": {"campaign_id": "123", "current_daily_budget": 100, "daily_budget": 108},
        }).json()["id"]
        approval = store.get_approval(workspace_id, low)
        decision = evaluate_autopilot_policy(workspace_id, approval)
        assert decision["eligible"] is True

        high = client.post(f"/api/approvals?workspace_id={workspace_id}", json={
            "action_type": "google.pause_campaign",
            "title": "Pause campaign",
            "description": "High risk pause",
            "provider": "google",
            "risk_level": "high",
            "payload": {"campaign_id": "123"},
        }).json()["id"]
        high_decision = client.get(f"/api/autopilot/evaluate/{high}?workspace_id={workspace_id}").json()
        assert high_decision["eligible"] is False
        assert any("High-risk" in reason for reason in high_decision["reasons"])

        monkeypatch.delenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", raising=False)
        run = client.post(f"/api/autopilot/run-once?workspace_id={workspace_id}")
        assert run.status_code == 200
        assert run.json()["disabled"] is True


def test_password_reset_and_stripe_readiness(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "auth06.db")
    monkeypatch.setenv("VEZMORA_DEV_SHOW_TOKENS", "true")
    store.init_db()
    with TestClient(app) as client:
        workspace_id = register(client, "reset06@example.com")
        billing = client.get(f"/api/billing?workspace_id={workspace_id}").json()
        assert billing["billing_status"] == "trialing"
        assert billing["trial_active"] is True

        client.post("/api/auth/logout")
        req = client.post("/api/auth/password-reset/request", json={"email": "reset06@example.com"})
        assert req.status_code == 200
        token = req.json()["dev_reset_token"]
        confirm = client.post("/api/auth/password-reset/confirm", json={"token": token, "password": "newsecurepass123"})
        assert confirm.status_code == 200
        login = client.post("/api/auth/login", json={"email": "reset06@example.com", "password": "newsecurepass123"})
        assert login.status_code == 200

        checkout = client.post(f"/api/billing/checkout?workspace_id={workspace_id}", json={"plan": "growth"})
        assert checkout.status_code == 503


def test_health_reports_private_beta(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "health06.db")
    store.init_db()
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["version"] == "0.6.1"
        assert "autopilot_execution_enabled" in health
        assert "stripe_configured" in health
        assert "smtp_configured" in health
