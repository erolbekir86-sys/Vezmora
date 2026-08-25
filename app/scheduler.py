from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .agent import generate_daily_brief
from .briefs import brief_memory, create_metric_proposals
from .models import CompanyProfile
from .monitor import scan_all_competitors
from .autopilot import autopilot_runtime_enabled, run_autopilot_once
from .store import (
    add_notification,
    get_company_profile,
    list_competitors,
    list_enabled_brief_settings,
    mark_daily_brief_run,
    save_run,
    list_autopilot_workspaces,
)


def scheduler_enabled() -> bool:
    return os.getenv("VEZMORA_ENABLE_SCHEDULER", "0").lower() in {"1", "true", "yes", "on"}


async def run_due_automation_once() -> dict[str, int]:
    counts = {"briefs": 0, "rival_scans": 0, "autopilot_runs": 0}
    now_utc = datetime.now(timezone.utc)

    if os.getenv("OPENAI_API_KEY"):
        for settings in list_enabled_brief_settings():
            try:
                tz = ZoneInfo(settings["timezone"])
            except ZoneInfoNotFoundError:
                add_notification(settings["workspace_id"], "scheduler", "Daily brief skipped", f"Unknown timezone: {settings['timezone']}")
                continue
            local_now = now_utc.astimezone(tz)
            today = local_now.date().isoformat()
            if local_now.hour < int(settings["hour"]) or settings.get("last_run_date") == today:
                continue
            company_data = get_company_profile(int(settings["workspace_id"]))
            if not company_data:
                continue
            company = CompanyProfile.model_validate(company_data)
            workspace_id = int(settings["workspace_id"])
            try:
                output = await generate_daily_brief(company, brief_memory(workspace_id))
                save_run("brief", company.name, company.language, {"scheduled": True}, output, workspace_id, None)
                created = create_metric_proposals(workspace_id, None)
                add_notification(workspace_id, "brief", "Morning brief ready", f"Vezmora created today's brief. {len(created)} approval proposal(s) added.")
                mark_daily_brief_run(workspace_id, today)
                counts["briefs"] += 1
            except Exception as exc:
                add_notification(workspace_id, "scheduler", "Morning brief failed", f"{type(exc).__name__}")

    scan_hours = max(1, int(os.getenv("VEZMORA_RIVAL_SCAN_HOURS", "12")))
    for settings in list_enabled_brief_settings():
        workspace_id = int(settings["workspace_id"])
        competitors = list_competitors(workspace_id)
        due = False
        for competitor in competitors:
            checked = competitor.get("last_checked_at")
            if not checked:
                due = True
                break
            try:
                checked_dt = datetime.fromisoformat(checked.replace("Z", "+00:00"))
                if checked_dt.tzinfo is None:
                    checked_dt = checked_dt.replace(tzinfo=timezone.utc)
                if (now_utc - checked_dt.astimezone(timezone.utc)).total_seconds() >= scan_hours * 3600:
                    due = True
                    break
            except ValueError:
                due = True
                break
        if due and competitors:
            try:
                await scan_all_competitors(workspace_id)
                counts["rival_scans"] += 1
            except Exception:
                pass
    if autopilot_runtime_enabled():
        for workspace_id in list_autopilot_workspaces():
            try:
                result = await run_autopilot_once(workspace_id)
                if int(result.get("executed", 0)) or int(result.get("skipped", 0)):
                    counts["autopilot_runs"] += 1
            except Exception:
                pass
    return counts


async def scheduler_loop() -> None:
    while True:
        try:
            await run_due_automation_once()
        except Exception:
            pass
        await asyncio.sleep(900)
