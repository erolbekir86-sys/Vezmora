from __future__ import annotations

import asyncio
import os
from typing import Any

from .analytics import detect_anomalies
from .connectors import sync_all, sync_google, sync_meta
from .monitor import scan_all_competitors
from .store import claim_job, fail_job, finish_job, get_company_profile, get_onboarding_profile, record_usage, save_run, add_notification
from .agent import generate_daily_brief, generate_strategy
from .briefs import brief_memory
from .models import CompanyProfile, StrategyRequest
from .autopilot import run_autopilot_once
from .emailer import run_email_once


async def execute_job(job: dict[str, Any]) -> dict[str, Any]:
    workspace_id = int(job["workspace_id"])
    kind = str(job["kind"])
    payload = job.get("payload") or {}
    days = int(payload.get("days", 7))
    if kind == "sync_all":
        return await sync_all(workspace_id, days)
    if kind == "sync_google":
        return await sync_google(workspace_id, days)
    if kind == "sync_meta":
        return await sync_meta(workspace_id, days)
    if kind == "scan_rivals":
        return {"results": await scan_all_competitors(workspace_id)}
    if kind == "detect_anomalies":
        return {"anomalies": detect_anomalies(workspace_id)}
    if kind == "autopilot_tick":
        return await run_autopilot_once(workspace_id)
    if kind == "initial_strategy":
        company_data = get_company_profile(workspace_id)
        if not company_data:
            raise RuntimeError("Company profile is required for the initial strategy")
        company = CompanyProfile.model_validate(company_data)
        onboarding = get_onboarding_profile(workspace_id).get("data") or {}
        request = StrategyRequest(
            company=company,
            objective=payload.get("objective") or onboarding.get("primary_goal") or "sales",
            budget_sek=int(payload.get("budget") or onboarding.get("monthly_budget") or 0) or None,
            horizon_days=int(payload.get("horizon_days") or 30),
            notes="Private Beta onboarding plan. Prioritize the fastest measurable route to the stated growth target.",
        )
        output = await generate_strategy(request, brief_memory(workspace_id))
        run_id = save_run("strategy", company.name, company.language, {"job_id": job["id"], "source": "onboarding"}, output, workspace_id, None)
        record_usage(workspace_id, "ai_runs", 1, {"kind": "initial_strategy"})
        add_notification(workspace_id, "core", "Your first 30-day plan is ready", "Open Pulse to review the onboarding strategy.", {"run_id": run_id})
        return {"run_id": run_id}
    if kind == "daily_brief":
        company_data = get_company_profile(workspace_id)
        if not company_data:
            raise RuntimeError("Company profile is required for a daily brief")
        company = CompanyProfile.model_validate(company_data)
        output = await generate_daily_brief(company, brief_memory(workspace_id))
        run_id = save_run("brief", company.name, company.language, {"job_id": job["id"]}, output, workspace_id, None)
        return {"run_id": run_id}
    raise RuntimeError(f"Unknown job kind: {kind}")


async def run_worker_once() -> bool:
    job = claim_job()
    if not job:
        return False
    try:
        result = await execute_job(job)
        finish_job(int(job["id"]), result)
    except Exception as exc:
        retry = int(job.get("attempts", 1)) < 3
        fail_job(int(job["id"]), f"{type(exc).__name__}: {exc}", retry=retry)
    return True


async def worker_loop() -> None:
    poll_seconds = max(1, int(os.getenv("VEZMORA_WORKER_POLL_SECONDS", "5")))
    while True:
        did_work = await run_worker_once()
        did_email = await asyncio.to_thread(run_email_once)
        if not did_work and not did_email:
            await asyncio.sleep(poll_seconds)


def worker_enabled() -> bool:
    return os.getenv("VEZMORA_ENABLE_WORKER", "0").lower() in {"1", "true", "yes", "on"}
