from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException

from .execution import execute_approved_action, execution_enabled
from .store import (
    add_notification,
    decide_approval,
    get_autopilot_settings,
    list_approvals,
    log_execution,
    set_approval_execution_status,
    workspace_daily_execution_spend,
)


def autopilot_runtime_enabled() -> bool:
    return os.getenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", "0").lower() in {"1", "true", "yes", "on"}


def evaluate_autopilot_policy(workspace_id: int, approval: dict[str, Any]) -> dict[str, Any]:
    settings = get_autopilot_settings(workspace_id)
    action_type = str(approval.get("action_type") or "")
    payload = approval.get("payload") or {}
    reasons: list[str] = []

    if settings["mode"] != "autopilot":
        reasons.append("Workspace is not in Autopilot mode")
    if action_type not in set(settings.get("allowed_actions") or []):
        reasons.append("Action type is not pre-approved in this workspace")
    if str(approval.get("risk_level") or "medium") == "high":
        reasons.append("High-risk actions always require a human in Private Beta")

    cap = float(settings.get("daily_spend_cap") or 0)
    today_total = workspace_daily_execution_spend(workspace_id)
    requested = 0.0
    for key in ("daily_budget", "budget", "amount"):
        if payload.get(key) is not None:
            try:
                requested = max(0.0, float(payload[key]))
            except (TypeError, ValueError):
                requested = 0.0
            break
    if cap > 0 and requested > 0 and today_total + requested > cap:
        reasons.append(f"Daily safety cap would be exceeded ({today_total + requested:.2f} > {cap:.2f})")

    if action_type == "google.set_daily_budget":
        new_budget = float(payload.get("daily_budget") or 0)
        current_budget = float(payload.get("current_daily_budget") or 0)
        if new_budget <= 0 or current_budget <= 0:
            reasons.append("Autopilot budget changes require current_daily_budget evidence")
        else:
            pct = abs(new_budget - current_budget) / current_budget * 100
            max_pct = float(settings.get("max_budget_change_pct") or 0)
            if pct > max_pct:
                reasons.append(f"Budget change {pct:.1f}% exceeds workspace limit {max_pct:.1f}%")

    return {
        "eligible": not reasons,
        "mode": settings["mode"],
        "action_type": action_type,
        "reasons": reasons,
        "runtime_execution_enabled": execution_enabled(),
        "autopilot_runtime_enabled": autopilot_runtime_enabled(),
        "policy": settings,
    }


async def run_autopilot_once(workspace_id: int, limit: int = 5) -> dict[str, Any]:
    if not autopilot_runtime_enabled():
        return {"executed": 0, "skipped": 0, "disabled": True, "reason": "VEZMORA_AUTOPILOT_EXECUTION_ENABLED is off"}
    if not execution_enabled():
        return {"executed": 0, "skipped": 0, "disabled": True, "reason": "VEZMORA_EXECUTION_ENABLED is off"}

    executed = 0
    skipped = 0
    details: list[dict[str, Any]] = []
    for approval in list_approvals(workspace_id, "pending", max(1, min(limit, 20))):
        decision = evaluate_autopilot_policy(workspace_id, approval)
        if not decision["eligible"]:
            skipped += 1
            details.append({"approval_id": approval["id"], "status": "skipped", "reasons": decision["reasons"]})
            continue

        if not decide_approval(workspace_id, int(approval["id"]), None, "approved", "Auto-approved by workspace Autopilot policy"):
            skipped += 1
            continue
        approval = dict(approval)
        approval["status"] = "approved"
        try:
            result = await execute_approved_action(workspace_id, approval)
            set_approval_execution_status(workspace_id, int(approval["id"]), "executed")
            log_execution(
                workspace_id,
                int(approval["id"]),
                None,
                str(approval.get("provider") or approval["action_type"].split(".", 1)[0]),
                str(approval["action_type"]),
                approval.get("payload") or {},
                result,
                "executed",
            )
            add_notification(workspace_id, "autopilot", "Autopilot executed an action", str(approval.get("title") or "Action"), {"approval_id": approval["id"]})
            executed += 1
            details.append({"approval_id": approval["id"], "status": "executed"})
        except HTTPException as exc:
            set_approval_execution_status(workspace_id, int(approval["id"]), "failed")
            log_execution(
                workspace_id,
                int(approval["id"]),
                None,
                str(approval.get("provider") or "unknown"),
                str(approval["action_type"]),
                approval.get("payload") or {},
                {"error": str(exc.detail)},
                "failed",
            )
            details.append({"approval_id": approval["id"], "status": "failed", "error": str(exc.detail)})
    return {"executed": executed, "skipped": skipped, "disabled": False, "details": details}
