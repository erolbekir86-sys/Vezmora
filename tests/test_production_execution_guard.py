from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import SESSION_COOKIE
from app.production_execution_guard import install_production_execution_guard


ROOT = Path(__file__).resolve().parents[1]
INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
ENV_GUARDS = (ROOT / "app" / "production_env_guards.py").read_text(encoding="utf-8")


def _guarded_app() -> FastAPI:
    app = FastAPI()

    @app.post("/api/executions/{approval_id}/run")
    def execute(approval_id: int):
        return {"reached": True, "approval_id": approval_id}

    @app.get("/api/executions/{approval_id}/preview")
    def preview(approval_id: int):
        return {"preview": True, "approval_id": approval_id}

    @app.post("/api/autopilot/run-once")
    def autopilot():
        return {"reached": True}

    @app.post("/api/approvals/1/approve")
    def approve():
        return {"reached": True}

    install_production_execution_guard(app)
    return app


def test_vercel_authenticated_execution_routes_are_hard_locked(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(_guarded_app()) as client:
        client.cookies.set(SESSION_COOKIE, "test-session")
        execution = client.post("/api/executions/123/run", json={"confirm": True})
        autopilot = client.post("/api/autopilot/run-once")

    for response in (execution, autopilot):
        assert response.status_code == 409
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["detail"] == (
            "External execution is disabled in Vexmera Private Beta. "
            "Review and recommendation features remain available."
        )


def test_guard_preserves_unauthenticated_and_local_route_handling(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(_guarded_app()) as client:
        no_cookie = client.post("/api/autopilot/run-once")
    assert no_cookie.status_code == 200

    monkeypatch.delenv("VERCEL", raising=False)
    with TestClient(_guarded_app()) as client:
        client.cookies.set(SESSION_COOKIE, "test-session")
        local = client.post("/api/autopilot/run-once")
    assert local.status_code == 200


def test_preview_and_non_execution_mutations_remain_available_on_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(_guarded_app()) as client:
        client.cookies.set(SESSION_COOKIE, "test-session")
        preview = client.get("/api/executions/123/preview")
        approval = client.post("/api/approvals/1/approve")

    assert preview.status_code == 200
    assert preview.json()["preview"] is True
    assert approval.status_code == 200


def test_guard_is_installed_and_existing_env_lock_remains_the_first_barrier():
    assert "install_production_execution_guard" in INIT
    assert "VEZMORA_EXECUTION_ENABLED" in ENV_GUARDS
    assert "VEZMORA_AUTOPILOT_EXECUTION_ENABLED" in ENV_GUARDS
    assert "os.environ[name] = \"false\"" in ENV_GUARDS


def test_guard_is_narrow_and_contains_no_provider_or_business_mutations():
    source = (ROOT / "app" / "production_execution_guard.py").read_text(encoding="utf-8")
    assert "request.method.upper() != \"POST\"" in source
    assert "^/api/executions/\\d+/run/?$" in source
    assert "/api/autopilot/run-once" in source
    for forbidden in (
        "httpx",
        "requests",
        "STRIPE_SECRET_KEY",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
        "ads_management",
        "campaigns:mutate",
        "campaignBudgets:mutate",
    ):
        assert forbidden not in source
