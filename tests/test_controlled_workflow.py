from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from http.cookies import SimpleCookie

import pytest
from fastapi import HTTPException, Response
from fastapi.testclient import TestClient

from app import jobs, scheduler, store, usage_controls
import app.main as main
from app.campaign_workflow import queue_campaign_run


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "controlled.db")
    store.init_db()
    user_id, workspace_id = store.create_user("owner@example.com", "salt", "hash", "Pilot")
    return user_id, workspace_id


def test_simultaneous_runs_share_one_hard_cap(workspace):
    _, ws = workspace
    usage_controls.set_monthly_limit(ws, 3)

    def reserve(_):
        try:
            return usage_controls.reserve_run(ws, "agent", "manual")
        except HTTPException as exc:
            assert exc.status_code == 402
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        reservations = list(pool.map(reserve, range(12)))
    assert len([r for r in reservations if r]) == 3
    summary = usage_controls.usage_overview(ws)
    assert summary["used"] == 3
    assert summary["blocked"] is True
    assert summary["remaining"] == 0


def test_failed_generation_releases_capacity_and_plan_stays_ceiling(workspace):
    _, ws = workspace
    usage_controls.set_monthly_limit(ws, 1)

    async def fail():
        raise RuntimeError("provider unavailable")

    with pytest.raises(RuntimeError):
        asyncio.run(usage_controls.run_metered(ws, "agent", fail))
    assert usage_controls.usage_overview(ws)["used"] == 0

    async def success():
        return "complete"

    assert asyncio.run(usage_controls.run_metered(ws, "agent", success)) == "complete"
    assert usage_controls.usage_overview(ws)["recent"][0]["state"] == "completed"
    usage_controls.set_monthly_limit(ws, 999999)
    assert usage_controls.usage_overview(ws)["effective_limit"] == 100
    usage_controls.set_monthly_limit(ws, 0)
    with pytest.raises(HTTPException):
        asyncio.run(usage_controls.run_metered(ws, "agent", success))


def test_prior_month_usage_and_other_workspace_do_not_reduce_capacity(workspace):
    user, ws = workspace
    other = store.create_workspace(user, "Other")
    store.record_usage(ws, "ai_runs", 90)
    with store._connect() as con:
        con.execute("UPDATE usage_events SET created_at='2000-01-01 00:00:00' WHERE workspace_id=?", (ws,))
    usage_controls.set_monthly_limit(ws, 1)
    usage_controls.set_monthly_limit(other, 1)
    usage_controls.reserve_run(other, "agent", "manual")
    usage_controls.reserve_run(ws, "campaign", "manual")
    assert usage_controls.usage_overview(ws)["used"] == 1


def test_worker_and_scheduler_cannot_bypass_paused_workspace(workspace, monkeypatch):
    _, ws = workspace
    store.save_company_profile(ws, {"name": "Pilot", "industry": "Retail", "market": "Sweden", "audience": "Local customers", "offer": "Goods", "brand_voice": "Clear", "language": "sv"})
    usage_controls.set_monthly_limit(ws, 0)
    calls = []

    async def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("model must not run past quota")

    monkeypatch.setattr(jobs, "generate_daily_brief", forbidden)
    monkeypatch.setattr(jobs, "generate_strategy", forbidden)
    for kind in ("daily_brief", "initial_strategy"):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(jobs.execute_job({"id": 1, "workspace_id": ws, "kind": kind, "payload": {}}))
        assert exc.value.status_code == 402
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr(scheduler, "generate_daily_brief", forbidden)
    monkeypatch.setattr(scheduler, "list_enabled_brief_settings", lambda: [{"workspace_id": ws, "timezone": "UTC", "hour": 0, "last_run_date": None}])
    monkeypatch.setattr(scheduler, "list_competitors", lambda _: [])
    monkeypatch.setattr(scheduler, "list_autopilot_workspaces", lambda: [])
    assert asyncio.run(scheduler.run_due_automation_once())["briefs"] == 0
    assert not calls
    assert usage_controls.usage_overview(ws)["used"] == 0


def test_campaign_queue_uses_saved_snapshot_and_is_idempotent(workspace):
    user, ws = workspace
    output = "Approved source content. " * 400  # Longer than the public free-text create limit.
    run = store.save_run("campaign", "Pilot", "sv", {"campaign_name": "Saved name", "channel": "meta", "budget_sek": 1234, "objective": "sales"}, output, ws, user)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: queue_campaign_run(ws, run, user), range(4)))
    assert len({r["id"] for r in results}) == 1
    assert sum(r["created"] for r in results) == 1
    approval = store.get_approval(ws, results[0]["id"])
    assert approval["description"] == output
    assert approval["title"] == "Launch: Saved name"
    assert approval["payload"]["source_run_id"] == run
    assert approval["payload"]["budget_sek"] == 1234
    other = store.create_workspace(user, "Other")
    with pytest.raises(HTTPException) as exc:
        queue_campaign_run(other, run, user)
    assert exc.value.status_code == 404


def test_api_limits_roles_and_review_timeline(workspace, monkeypatch):
    owner, ws = workspace
    viewer, _ = store.create_user("viewer@example.com", "salt", "hash", "Own")
    store.add_workspace_member(ws, viewer, "viewer")
    run = store.save_run("campaign", "Pilot", "sv", {"campaign_name": "Spring", "channel": "meta"}, "A saved campaign proposal", ws, owner)
    monkeypatch.setattr(main, "_require_key", lambda: None)
    with TestClient(main.app) as client:
        # Auth's real cookie is set from an actual session rather than bypassing dependencies.
        from app.auth import SESSION_COOKIE, start_session
        def login(user_id):
            response = Response()
            start_session(response, user_id)
            cookie = SimpleCookie(response.headers["set-cookie"])
            client.cookies.set(SESSION_COOKIE, cookie[SESSION_COOKIE].value)

        login(owner)
        assert client.put(f"/api/usage/controls?workspace_id={ws}", json={"monthly_run_limit": -1}).status_code == 422
        assert client.put(f"/api/usage/controls?workspace_id={ws}", json={"monthly_run_limit": 0}).status_code == 200
        # Supply a company so profile validation cannot mask the limit.
        store.save_company_profile(ws, {"name": "Pilot", "industry": "Retail", "market": "Sweden", "audience": "Local customers", "offer": "Goods", "brand_voice": "Clear", "language": "sv"})
        response = client.post(f"/api/agent?workspace_id={ws}", json={"message": "Help me plan growth"})
        assert response.status_code == 402, response.text
        queued = client.post(f"/api/runs/{run}/queue?workspace_id={ws}")
        assert queued.status_code == 200, queued.text
        approval_id = queued.json()["id"]
        review_url = f"/api/approvals/{approval_id}/review?workspace_id={ws}"
        review = client.get(review_url).json()
        assert review["supported"] is False
        assert review["can_review"] is True
        assert [r["event"] for r in review["timeline"]] == ["created"]
        assert client.post(f"/api/approvals/{approval_id}/approve?workspace_id={ws}", json={"note": "Fits our budget"}).status_code == 200
        review = client.get(review_url).json()
        assert review["timeline"][-1]["note"] == "Fits our budget"
        assert review["approval"]["status"] == "approved"
        assert store.list_executions(ws) == []
        login(viewer)
        assert client.get(f"/api/usage?workspace_id={ws}").json()["can_manage"] is False
        assert client.put(f"/api/usage/controls?workspace_id={ws}", json={"monthly_run_limit": 1}).status_code == 403
        assert client.post(f"/api/runs/{run}/queue?workspace_id={ws}").status_code == 403
        assert client.get(review_url).json()["can_review"] is False
        outsider, outside_ws = store.create_user("outsider@example.com", "salt", "hash", "Outside")
        login(outsider)
        assert client.get(review_url).status_code == 403
        assert client.get(f"/api/approvals/{approval_id}/review?workspace_id={outside_ws}").status_code == 404


def test_successful_background_generations_are_counted(workspace, monkeypatch):
    _, ws = workspace
    store.save_company_profile(ws, {"name": "Pilot", "industry": "Retail", "market": "Sweden", "audience": "Local customers", "offer": "Goods", "brand_voice": "Clear", "language": "sv"})

    async def generate(*args):
        return "A saved plan or briefing"

    monkeypatch.setattr(jobs, "generate_daily_brief", generate)
    monkeypatch.setattr(jobs, "generate_strategy", generate)
    monkeypatch.setattr(scheduler, "generate_daily_brief", generate)
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr(scheduler, "list_enabled_brief_settings", lambda: [{"workspace_id": ws, "timezone": "UTC", "hour": 0, "last_run_date": None}])
    monkeypatch.setattr(scheduler, "list_competitors", lambda _: [])
    monkeypatch.setattr(scheduler, "list_autopilot_workspaces", lambda: [])
    for kind in ("daily_brief", "initial_strategy"):
        asyncio.run(jobs.execute_job({"id": 1, "workspace_id": ws, "kind": kind, "payload": {}}))
    assert asyncio.run(scheduler.run_due_automation_once())["briefs"] == 1
    usage = usage_controls.usage_overview(ws)
    assert usage["used"] == 3
    assert usage["by_source"] == {"worker": 2, "scheduler": 1}
    assert all(row["state"] == "completed" for row in usage["recent"])
