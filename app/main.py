from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .agent import MODEL, generate_campaign, generate_daily_brief, generate_strategy, run_agent
from .auth import end_session, hash_password, require_user, start_session, verify_password
from .briefs import brief_memory, create_metric_proposals
from .analytics import detect_anomalies
from .billing import billing_status, enforce_limit
from .execution import execution_enabled, execute_approved_action, preview_external
from .autopilot import autopilot_runtime_enabled, evaluate_autopilot_policy, run_autopilot_once
from .core import core_today
from .emailer import app_url as email_app_url, smtp_configured, run_email_once
from .currency import base_currency, convert_to_base
from .jobs import worker_enabled, worker_loop, run_worker_once
from .connectors import (
    connector_readiness,
    google_authorization_url,
    google_callback,
    meta_authorization_url,
    meta_callback,
    save_connector_settings,
    sync_all,
    sync_google,
    sync_meta,
)
from .models import (
    AgentRequest,
    AgentResponse,
    ApprovalCreate,
    ApprovalDecision,
    CampaignRequest,
    CompanyProfile,
    CompetitorCreate,
    ConnectorSettings,
    DailyBriefSettings,
    FXRateUpsert,
    KPIEntry,
    JobCreateRequest,
    LoginRequest,
    RegisterRequest,
    StrategyRequest,
    SyncRequest,
    TeamInviteRequest,
    TeamJoinRequest,
    WorkspaceCreate,
    WorkspaceSettings,
    ApprovalExecuteRequest,
    AutopilotSettings,
    BetaFeedbackCreate,
    BillingCheckoutRequest,
    OnboardingProfile,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from .monitor import scan_all_competitors, scan_competitor
from .stripe_billing import apply_webhook, create_checkout, create_portal, parse_webhook, stripe_configured
from .scheduler import scheduler_enabled, scheduler_loop, run_due_automation_once
from .store import (
    add_competitor,
    add_kpi,
    add_workspace_member,
    add_notification,
    create_approval,
    create_user,
    create_workspace_invite,
    create_workspace,
    dashboard_summary,
    decide_approval,
    consume_workspace_invite,
    enqueue_job,
    delete_competitor,
    delete_kpi,
    get_company_profile,
    get_connectors,
    get_approval,
    get_user_by_email,
    get_workspace_role,
    get_workspace_settings,
    get_daily_brief_settings,
    init_db,
    latest_run,
    list_approvals,
    list_anomalies,
    list_campaign_metrics,
    campaign_summary,
    list_competitors,
    list_executions,
    list_fx_rates,
    list_jobs,
    list_kpis,
    list_notifications,
    list_workspace_members,
    list_workspaces,
    mark_notification_read,
    recent_competitor_changes,
    recent_runs,
    save_company_profile,
    save_daily_brief_settings,
    save_workspace_settings,
    set_approval_execution_status,
    log_execution,
    record_usage,
    upsert_fx_rate,
    save_run,
    storage_backend,
    user_has_workspace,
    add_beta_feedback,
    create_password_reset,
    get_autopilot_settings,
    get_onboarding_profile,
    queue_email,
    save_autopilot_settings,
    save_onboarding_profile,
    set_workspace_billing,
    update_user_password,
    consume_password_reset,
)

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"


def serverless_mode() -> bool:
    return os.getenv("VEZMORA_SERVERLESS", "0").lower() in {"1", "true", "yes", "on"}


def _require_cron(authorization: str | None) -> None:
    secret = os.getenv("CRON_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not configured")
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized cron request")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    tasks: list[asyncio.Task] = []
    if not serverless_mode() and scheduler_enabled():
        tasks.append(asyncio.create_task(scheduler_loop(), name="vezmora-scheduler"))
    if not serverless_mode() and worker_enabled():
        tasks.append(asyncio.create_task(worker_loop(), name="vezmora-worker"))
    yield
    for task in tasks:
        task.cancel()
    for task in tasks:
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Vezmora API", version="0.6.1", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "vezmora",
        "version": "0.6.1",
        "model": MODEL,
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "oauth_secret_configured": bool(os.getenv("VEZMORA_SECRET_KEY")),
        "scheduler_enabled": scheduler_enabled(),
        "worker_enabled": worker_enabled(),
        "execution_enabled": execution_enabled(),
        "autopilot_execution_enabled": autopilot_runtime_enabled(),
        "stripe_configured": stripe_configured(),
        "smtp_configured": smtp_configured(),
        "serverless_mode": serverless_mode(),
        "storage_backend": storage_backend(),
        "data_path": "remote" if storage_backend() == "turso" else str(os.getenv("VEZMORA_DB_PATH") or (Path(os.getenv("VEZMORA_DATA_DIR", str(ROOT))) / ".vezmora.db")),
    }


User = Annotated[dict[str, Any], Depends(require_user)]


def _workspace(user: dict[str, Any], workspace_id: int) -> int:
    if not user_has_workspace(int(user["id"]), workspace_id):
        raise HTTPException(status_code=403, detail="Workspace access denied")
    return workspace_id


def _require_role(user: dict[str, Any], workspace_id: int, allowed: set[str]) -> str:
    _workspace(user, workspace_id)
    role = get_workspace_role(int(user["id"]), workspace_id)
    if role not in allowed:
        raise HTTPException(status_code=403, detail=f"This action requires one of these roles: {', '.join(sorted(allowed))}")
    return str(role)


def _company_for(workspace_id: int, supplied: CompanyProfile | None) -> CompanyProfile:
    if supplied is not None:
        save_company_profile(workspace_id, supplied.model_dump(mode="json"))
        return supplied
    saved = get_company_profile(workspace_id)
    if not saved:
        raise HTTPException(status_code=400, detail="Save a company profile before running Vezmora")
    return CompanyProfile.model_validate(saved)


def _memory(workspace_id: int) -> dict[str, Any]:
    return {
        "kpi_summary": dashboard_summary(workspace_id),
        "competitors": [
            {"name": c["name"], "url": c["url"], "notes": c["notes"], "last_changed": c.get("last_changed")}
            for c in list_competitors(workspace_id)[:10]
        ],
        "recent_competitor_changes": recent_competitor_changes(workspace_id, 10),
        "campaign_performance_30d": campaign_summary(workspace_id, 30)[:20],
        "recent_anomalies": list_anomalies(workspace_id, 10),
        "pending_approvals": list_approvals(workspace_id, "pending", 10),
        "commercial_brief": get_onboarding_profile(workspace_id),
        "autopilot_policy": get_autopilot_settings(workspace_id),
    }


def _require_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured for this runtime")


@app.post("/api/auth/register")
def register(request: RegisterRequest, response: Response) -> dict[str, Any]:
    salt, password_hash = hash_password(request.password)
    try:
        user_id, workspace_id = create_user(str(request.email), salt, password_hash, request.workspace_name)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with that email already exists") from exc
    set_workspace_billing(workspace_id, billing_status="trialing", trial_ends_at=(datetime.now(timezone.utc) + timedelta(days=14)).isoformat())
    start_session(response, user_id)
    return {"ok": True, "user": {"id": user_id, "email": str(request.email)}, "workspace_id": workspace_id}


@app.post("/api/auth/login")
def login(request: LoginRequest, response: Response) -> dict[str, Any]:
    user = get_user_by_email(str(request.email))
    if not user or not verify_password(request.password, user["password_salt"], user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    start_session(response, int(user["id"]))
    return {"ok": True, "user": {"id": user["id"], "email": user["email"]}, "workspaces": list_workspaces(int(user["id"]))}


@app.post("/api/auth/logout")
def logout(response: Response, vezmora_session: str | None = Cookie(default=None)) -> dict[str, bool]:
    end_session(response, vezmora_session)
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: User) -> dict[str, Any]:
    return {"user": {"id": user["id"], "email": user["email"]}, "workspaces": list_workspaces(int(user["id"]))}


@app.get("/api/workspaces")
def workspaces(user: User) -> list[dict[str, Any]]:
    return list_workspaces(int(user["id"]))


@app.post("/api/workspaces")
def workspace_create(request: WorkspaceCreate, user: User) -> dict[str, Any]:
    workspace_id = create_workspace(int(user["id"]), request.name)
    return {"id": workspace_id, "name": request.name, "role": "owner"}


@app.get("/api/company")
def company_get(workspace_id: int, user: User) -> dict[str, Any] | None:
    _workspace(user, workspace_id)
    return get_company_profile(workspace_id)


@app.put("/api/company")
def company_put(workspace_id: int, profile: CompanyProfile, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin","marketer"})
    save_company_profile(workspace_id, profile.model_dump(mode="json"))
    return {"ok": True}


@app.post("/api/strategy", response_model=AgentResponse)
async def strategy(workspace_id: int, request: StrategyRequest, user: User) -> AgentResponse:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); _require_key(); enforce_limit(workspace_id, "ai_runs")
    company = _company_for(workspace_id, request.company); request.company = company
    try:
        output = await generate_strategy(request, _memory(workspace_id))
        save_run("strategy", company.name, company.language, request.model_dump(mode="json"), output, workspace_id, int(user["id"]))
        record_usage(workspace_id, "ai_runs", 1, {"kind":"strategy"})
        return AgentResponse(output=output, model=MODEL)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vezmora strategy run failed: {type(exc).__name__}") from exc


@app.post("/api/campaign", response_model=AgentResponse)
async def campaign(workspace_id: int, request: CampaignRequest, user: User) -> AgentResponse:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); _require_key(); enforce_limit(workspace_id, "ai_runs")
    company = _company_for(workspace_id, request.company); request.company = company
    try:
        output = await generate_campaign(request, _memory(workspace_id))
        save_run("campaign", company.name, company.language, request.model_dump(mode="json"), output, workspace_id, int(user["id"]))
        record_usage(workspace_id, "ai_runs", 1, {"kind":"campaign"})
        return AgentResponse(output=output, model=MODEL)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vezmora campaign run failed: {type(exc).__name__}") from exc


@app.post("/api/agent", response_model=AgentResponse)
async def agent(workspace_id: int, request: AgentRequest, user: User) -> AgentResponse:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); _require_key(); enforce_limit(workspace_id, "ai_runs")
    company = _company_for(workspace_id, request.company); request.company = company
    try:
        output = await run_agent(request, _memory(workspace_id))
        save_run("agent", company.name, company.language, request.model_dump(mode="json"), output, workspace_id, int(user["id"]))
        record_usage(workspace_id, "ai_runs", 1, {"kind":"agent"})
        return AgentResponse(output=output, model=MODEL)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vezmora agent run failed: {type(exc).__name__}") from exc


@app.get("/api/runs")
def runs(workspace_id: int, user: User, limit: int = 10) -> list[dict[str, object]]:
    _workspace(user, workspace_id)
    return recent_runs(max(1, min(limit, 50)), workspace_id)


@app.get("/api/kpis")
def kpis_get(workspace_id: int, user: User, limit: int = 90) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_kpis(workspace_id, max(1, min(limit, 3650)))


@app.post("/api/kpis")
def kpis_post(workspace_id: int, entry: KPIEntry, user: User) -> dict[str, int]:
    _require_role(user, workspace_id, {"owner","admin","marketer"})
    data = entry.model_dump(mode="json")
    source_currency = entry.currency.upper()
    data["spend_sek"] = convert_to_base(workspace_id, entry.spend_sek, source_currency)
    data["revenue_sek"] = convert_to_base(workspace_id, entry.revenue_sek, source_currency)
    data["currency"] = base_currency(workspace_id)
    return {"id": add_kpi(workspace_id, data)}


@app.delete("/api/kpis/{kpi_id}")
def kpis_delete(kpi_id: int, workspace_id: int, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); delete_kpi(workspace_id, kpi_id)
    return {"ok": True}


@app.get("/api/dashboard")
def dashboard(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    summary = dashboard_summary(workspace_id)
    summary["pending_approvals"] = len(list_approvals(workspace_id, "pending", 1000))
    summary["unread_notifications"] = len(list_notifications(workspace_id, 1000, unread_only=True))
    summary["base_currency"] = base_currency(workspace_id)
    summary["anomalies"] = len(list_anomalies(workspace_id, 1000))
    return summary


@app.get("/api/competitors")
def competitors_get(workspace_id: int, user: User) -> list[dict[str, Any]]:
    _workspace(user, workspace_id); return list_competitors(workspace_id)


@app.post("/api/competitors")
def competitors_post(workspace_id: int, competitor: CompetitorCreate, user: User) -> dict[str, int]:
    _require_role(user, workspace_id, {"owner","admin","marketer"})
    return {"id": add_competitor(workspace_id, competitor.name, str(competitor.url) if competitor.url else None, competitor.notes)}


@app.delete("/api/competitors/{competitor_id}")
def competitors_delete(competitor_id: int, workspace_id: int, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); delete_competitor(workspace_id, competitor_id); return {"ok": True}


@app.post("/api/competitors/{competitor_id}/scan")
async def competitor_scan(competitor_id: int, workspace_id: int, user: User) -> dict[str, object]:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); return await scan_competitor(workspace_id, competitor_id)


@app.post("/api/competitors/scan-all")
async def competitors_scan_all(workspace_id: int, user: User) -> list[dict[str, object]]:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); return await scan_all_competitors(workspace_id)


@app.get("/api/competitor-changes")
def competitor_changes(workspace_id: int, user: User, limit: int = 20) -> list[dict[str, Any]]:
    _workspace(user, workspace_id); return recent_competitor_changes(workspace_id, max(1, min(limit, 100)))


@app.get("/api/connectors")
def connectors_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    saved = {row["provider"]: row for row in get_connectors(workspace_id)}
    ready = connector_readiness()
    for provider, details in ready.items():
        details["connection"] = saved.get(provider, {"status": "disconnected", "metadata": {}})
    return ready


@app.put("/api/connectors/settings")
def connectors_settings(workspace_id: int, settings: ConnectorSettings, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin"}); save_connector_settings(workspace_id, settings.model_dump()); return {"ok": True}


@app.post("/api/connectors/{provider}/sync")
async def connector_sync(provider: str, workspace_id: int, request: SyncRequest, user: User) -> dict[str, object]:
    _require_role(user, workspace_id, {"owner","admin","marketer"})
    if provider == "google": return await sync_google(workspace_id, request.days)
    if provider == "meta": return await sync_meta(workspace_id, request.days)
    if provider == "all": return await sync_all(workspace_id, request.days)
    raise HTTPException(status_code=404, detail="Unknown connector")


@app.get("/api/connectors/google/start")
def google_start(workspace_id: int, user: User) -> dict[str, str]:
    _require_role(user, workspace_id, {"owner","admin"}); return {"authorization_url": google_authorization_url(workspace_id, int(user["id"]))}


@app.get("/api/connectors/google/callback")
async def google_oauth_callback(code: str = Query(...), state: str = Query(...)) -> RedirectResponse:
    await google_callback(code, state); return RedirectResponse(url="/?connected=google")


@app.get("/api/connectors/meta/start")
def meta_start(workspace_id: int, user: User) -> dict[str, str]:
    _require_role(user, workspace_id, {"owner","admin"}); return {"authorization_url": meta_authorization_url(workspace_id, int(user["id"]))}


@app.get("/api/connectors/meta/callback")
async def meta_oauth_callback(code: str = Query(...), state: str = Query(...)) -> RedirectResponse:
    await meta_callback(code, state); return RedirectResponse(url="/?connected=meta")


@app.get("/api/notifications")
def notifications(workspace_id: int, user: User, unread_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    _workspace(user, workspace_id); return list_notifications(workspace_id, max(1, min(limit, 100)), unread_only)


@app.post("/api/notifications/{notification_id}/read")
def notification_read(notification_id: int, workspace_id: int, user: User) -> dict[str, bool]:
    _workspace(user, workspace_id); mark_notification_read(workspace_id, notification_id); return {"ok": True}


@app.get("/api/approvals")
def approvals(workspace_id: int, user: User, status: str | None = None) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    if status not in {None, "pending", "approved", "rejected", "executed", "failed"}: raise HTTPException(status_code=400, detail="Invalid approval status")
    return list_approvals(workspace_id, status, 100)


@app.post("/api/approvals")
def approval_create(workspace_id: int, request: ApprovalCreate, user: User) -> dict[str, int]:
    _require_role(user, workspace_id, {"owner","admin","marketer"})
    approval_id = create_approval(workspace_id, int(user["id"]), request.action_type, request.title, request.description, request.provider, request.risk_level, request.payload)
    add_notification(workspace_id, "approval", "Approval requested", request.title, {"approval_id": approval_id})
    return {"id": approval_id}


@app.post("/api/approvals/{approval_id}/{decision}")
def approval_decide(approval_id: int, decision: str, workspace_id: int, request: ApprovalDecision, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin"})
    if decision not in {"approve", "reject"}: raise HTTPException(status_code=404, detail="Unknown decision")
    status = "approved" if decision == "approve" else "rejected"
    if not decide_approval(workspace_id, approval_id, int(user["id"]), status, request.note):
        raise HTTPException(status_code=409, detail="Approval is no longer pending")
    add_notification(workspace_id, "approval", f"Action {status}", f"Approval #{approval_id} was {status}. No external action was executed automatically.", {"approval_id": approval_id})
    return {"ok": True}


@app.get("/api/briefs/settings")
def brief_settings_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id); return get_daily_brief_settings(workspace_id)


@app.put("/api/briefs/settings")
def brief_settings_put(workspace_id: int, settings: DailyBriefSettings, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin"})
    try: ZoneInfo(settings.timezone)
    except ZoneInfoNotFoundError as exc: raise HTTPException(status_code=400, detail="Unknown timezone") from exc
    save_daily_brief_settings(workspace_id, settings.enabled, settings.hour, settings.timezone)
    return {"ok": True}


@app.get("/api/briefs/latest")
def brief_latest(workspace_id: int, user: User) -> dict[str, Any] | None:
    _workspace(user, workspace_id); return latest_run(workspace_id, "brief")


@app.post("/api/briefs/daily", response_model=AgentResponse)
async def daily_brief(workspace_id: int, user: User) -> AgentResponse:
    _require_role(user, workspace_id, {"owner","admin","marketer"}); _require_key(); enforce_limit(workspace_id, "ai_runs")
    company = _company_for(workspace_id, None)
    try:
        output = await generate_daily_brief(company, brief_memory(workspace_id))
        save_run("brief", company.name, company.language, {"manual": True}, output, workspace_id, int(user["id"]))
        record_usage(workspace_id, "ai_runs", 1, {"kind":"brief"})
        proposal_ids = create_metric_proposals(workspace_id, int(user["id"]))
        add_notification(workspace_id, "brief", "Executive brief ready", f"Brief created. {len(proposal_ids)} approval proposal(s) added.")
        return AgentResponse(output=output, model=MODEL)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vezmora brief failed: {type(exc).__name__}") from exc


@app.get("/api/workspace/settings")
def workspace_settings_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    return get_workspace_settings(workspace_id)


@app.put("/api/workspace/settings")
def workspace_settings_put(workspace_id: int, settings: WorkspaceSettings, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin"})
    save_workspace_settings(workspace_id, settings.base_currency.upper())
    return {"ok": True}


@app.get("/api/fx-rates")
def fx_rates_get(workspace_id: int, user: User) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_fx_rates(workspace_id)


@app.put("/api/fx-rates")
def fx_rates_put(workspace_id: int, rate: FXRateUpsert, user: User) -> dict[str, bool]:
    _require_role(user, workspace_id, {"owner","admin"})
    upsert_fx_rate(workspace_id, rate.quote_currency.upper(), rate.rate_to_base)
    return {"ok": True}


@app.get("/api/campaigns")
def campaigns_get(workspace_id: int, user: User, days: int = 30) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return campaign_summary(workspace_id, max(1, min(days, 365)))


@app.get("/api/campaign-metrics")
def campaign_metrics_get(workspace_id: int, user: User, limit: int = 300) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_campaign_metrics(workspace_id, max(1, min(limit, 5000)))


@app.get("/api/anomalies")
def anomalies_get(workspace_id: int, user: User, limit: int = 50) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_anomalies(workspace_id, max(1, min(limit, 200)))


@app.post("/api/anomalies/detect")
def anomalies_detect(workspace_id: int, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner","admin","marketer"})
    return {"anomalies": detect_anomalies(workspace_id)}


@app.get("/api/jobs")
def jobs_get(workspace_id: int, user: User, limit: int = 50) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_jobs(workspace_id, max(1, min(limit, 200)))


@app.post("/api/jobs")
async def jobs_post(workspace_id: int, request: JobCreateRequest, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner","admin"})
    enforce_limit(workspace_id, "jobs")
    job_id = enqueue_job(workspace_id, request.kind, request.payload)
    record_usage(workspace_id, "jobs", 1, {"kind": request.kind})
    processed_inline = False
    if serverless_mode():
        processed_inline = await run_worker_once()
    return {"id": job_id, "processed_inline": processed_inline}


@app.get("/api/team")
def team_get(workspace_id: int, user: User) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_workspace_members(workspace_id)


@app.post("/api/team/invites")
def team_invite(workspace_id: int, request: TeamInviteRequest, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner","admin"})
    status = billing_status(workspace_id)
    if len(list_workspace_members(workspace_id)) >= int(status["limits"]["team_members"]):
        raise HTTPException(status_code=402, detail="Team member limit reached for this plan")
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    invite_id = create_workspace_invite(workspace_id, str(request.email), request.role, token_hash, int(user["id"]), expires_at)
    invite_url = f"{email_app_url()}/?invite={raw}"
    queue_email(
        workspace_id,
        str(request.email),
        "You're invited to Vezmora",
        f"You were invited to a Vezmora workspace as {request.role}.\n\nOpen this link after creating or logging into your account:\n{invite_url}\n\nThis invite expires in 7 days.",
    )
    if serverless_mode() and smtp_configured():
        run_email_once()
    result = {"id": invite_id, "expires_at": expires_at, "delivery": "sent_or_queued" if smtp_configured() else "queued_smtp_not_configured"}
    if (not smtp_configured()) or os.getenv("VEZMORA_DEV_SHOW_TOKENS", "0").lower() in {"1","true","yes","on"}:
        result["invite_token"] = raw
    return result


@app.post("/api/team/join")
def team_join(request: TeamJoinRequest, user: User) -> dict[str, Any]:
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    invite = consume_workspace_invite(token_hash, str(user["email"]))
    if not invite:
        raise HTTPException(status_code=404, detail="Invite is invalid, expired, already used, or belongs to another email")
    add_workspace_member(int(invite["workspace_id"]), int(user["id"]), str(invite["role"]))
    return {"ok": True, "workspace_id": int(invite["workspace_id"]), "role": invite["role"]}


@app.get("/api/billing")
def billing_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    return billing_status(workspace_id)


@app.get("/api/executions")
def executions_get(workspace_id: int, user: User, limit: int = 50) -> list[dict[str, Any]]:
    _workspace(user, workspace_id)
    return list_executions(workspace_id, max(1, min(limit, 200)))


@app.get("/api/executions/{approval_id}/preview")
async def approval_preview(approval_id: int, workspace_id: int, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner","admin"})
    approval = get_approval(workspace_id, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return await preview_external(workspace_id, approval)


@app.post("/api/executions/{approval_id}/run")
async def approval_execute(approval_id: int, workspace_id: int, request: ApprovalExecuteRequest, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner","admin"})
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required")
    approval = get_approval(workspace_id, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    try:
        result = await execute_approved_action(workspace_id, approval)
        set_approval_execution_status(workspace_id, approval_id, "executed")
        log_execution(workspace_id, approval_id, int(user["id"]), str(approval.get("provider") or approval["action_type"].split(".",1)[0]), approval["action_type"], approval.get("payload") or {}, result, "executed")
        add_notification(workspace_id, "execution", "Approved action executed", approval["title"], {"approval_id": approval_id})
        return result
    except HTTPException as exc:
        log_execution(workspace_id, approval_id, int(user["id"]), str(approval.get("provider") or "unknown"), approval["action_type"], approval.get("payload") or {}, {"error": str(exc.detail)}, "failed")
        raise


# --- Vezmora 0.6 Private Beta ---

@app.get("/api/onboarding")
def onboarding_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    return get_onboarding_profile(workspace_id)


@app.put("/api/onboarding")
def onboarding_save(workspace_id: int, profile: OnboardingProfile, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner", "admin", "marketer"})
    save_onboarding_profile(workspace_id, profile.model_dump(mode="json"), complete=False)
    return {"ok": True, "completed": False}


@app.post("/api/onboarding/complete")
async def onboarding_complete(workspace_id: int, profile: OnboardingProfile, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner", "admin", "marketer"})
    try:
        ZoneInfo(profile.timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Unknown timezone") from exc
    company = CompanyProfile(
        name=profile.company_name,
        industry=profile.industry,
        market=profile.market,
        website=profile.website,
        audience=profile.audience,
        offer=profile.offer,
        brand_voice=profile.brand_voice,
        language=profile.language,
    )
    save_company_profile(workspace_id, company.model_dump(mode="json"))
    save_onboarding_profile(workspace_id, profile.model_dump(mode="json"), complete=True)
    current_brief = get_daily_brief_settings(workspace_id)
    save_daily_brief_settings(workspace_id, bool(current_brief.get("enabled")), int(current_brief.get("hour") or 8), profile.timezone)
    initial_strategy_queued = False
    if os.getenv("OPENAI_API_KEY"):
        enqueue_job(workspace_id, "initial_strategy", {"objective": profile.primary_goal, "budget": profile.monthly_budget, "horizon_days": 30})
        initial_strategy_queued = True
        if serverless_mode():
            await run_worker_once()
    add_notification(workspace_id, "onboarding", "Vezmora is ready", "Core now has your commercial brief and can prioritize against it. Your first 30-day plan is queued when AI runtime is configured.")
    return {"ok": True, "completed": True, "next": "core", "initial_strategy_queued": initial_strategy_queued}


@app.get("/api/core/today")
def core_today_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    return core_today(workspace_id)


@app.get("/api/autopilot")
def autopilot_get(workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    settings = get_autopilot_settings(workspace_id)
    settings["runtime_execution_enabled"] = execution_enabled()
    settings["autopilot_runtime_enabled"] = autopilot_runtime_enabled()
    return settings


@app.put("/api/autopilot")
def autopilot_put(workspace_id: int, settings: AutopilotSettings, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner", "admin"})
    save_autopilot_settings(
        workspace_id,
        settings.mode,
        settings.daily_spend_cap,
        settings.max_budget_change_pct,
        list(settings.allowed_actions),
    )
    add_notification(workspace_id, "autopilot", "Autopilot policy updated", f"Mode changed to {settings.mode}. External execution remains controlled by server safety switches.")
    return autopilot_get(workspace_id, user)


@app.get("/api/autopilot/evaluate/{approval_id}")
def autopilot_evaluate(approval_id: int, workspace_id: int, user: User) -> dict[str, Any]:
    _workspace(user, workspace_id)
    approval = get_approval(workspace_id, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return evaluate_autopilot_policy(workspace_id, approval)


@app.post("/api/autopilot/run-once")
async def autopilot_run_once(workspace_id: int, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner", "admin"})
    return await run_autopilot_once(workspace_id)


@app.post("/api/auth/password-reset/request")
def password_reset_request(request: PasswordResetRequest) -> dict[str, Any]:
    user = get_user_by_email(str(request.email))
    result: dict[str, Any] = {"ok": True, "message": "If that account exists, a reset link has been queued."}
    if user:
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_password_reset(int(user["id"]), token_hash, expires_at)
        reset_url = f"{email_app_url()}/?reset={raw}"
        queue_email(None, str(request.email), "Reset your Vezmora password", f"Use this link within 60 minutes to reset your Vezmora password:\n\n{reset_url}")
        if serverless_mode() and smtp_configured():
            run_email_once()
        if os.getenv("VEZMORA_DEV_SHOW_TOKENS", "0").lower() in {"1","true","yes","on"}:
            result["dev_reset_token"] = raw
    return result


@app.post("/api/auth/password-reset/confirm")
def password_reset_confirm(request: PasswordResetConfirm) -> dict[str, bool]:
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    user_id = consume_password_reset(token_hash)
    if not user_id:
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")
    salt, password_hash = hash_password(request.password)
    update_user_password(user_id, salt, password_hash)
    return {"ok": True}


@app.post("/api/beta/feedback")
def beta_feedback(workspace_id: int, request: BetaFeedbackCreate, user: User) -> dict[str, int]:
    _workspace(user, workspace_id)
    return {"id": add_beta_feedback(workspace_id, int(user["id"]), request.score, request.category, request.message)}


@app.post("/api/billing/checkout")
def billing_checkout(workspace_id: int, request: BillingCheckoutRequest, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner", "admin"})
    return create_checkout(workspace_id, str(user["email"]), request.plan)


@app.post("/api/billing/portal")
def billing_portal(workspace_id: int, user: User) -> dict[str, Any]:
    _require_role(user, workspace_id, {"owner", "admin"})
    return create_portal(workspace_id)


@app.post("/api/billing/webhook")
async def billing_webhook(request: Request, stripe_signature: str | None = Header(default=None, alias="Stripe-Signature")) -> dict[str, Any]:
    payload = await request.body()
    event = parse_webhook(payload, stripe_signature)
    return apply_webhook(event)


@app.get("/api/internal/cron/maintenance")
async def cron_maintenance(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    """Daily serverless catch-up for briefs, rivals, queued jobs and email."""
    _require_cron(authorization)
    automation = await run_due_automation_once()
    jobs_processed = 0
    for _ in range(10):
        if not await run_worker_once():
            break
        jobs_processed += 1
    emails_processed = 0
    for _ in range(10):
        if not await asyncio.to_thread(run_email_once):
            break
        emails_processed += 1
    return {
        "ok": True,
        "automation": automation,
        "jobs_processed": jobs_processed,
        "emails_processed": emails_processed,
    }


def main() -> None:
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
