"""Create reviewable campaign drafts from persisted, workspace-scoped runs."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from . import store
from .usage_controls import _locked_settings


def queue_campaign_run(workspace_id: int, run_id: int, user_id: int) -> dict[str, Any]:
    with store._connect() as con:
        _locked_settings(con, workspace_id)
        run = con.execute("SELECT * FROM runs WHERE workspace_id=? AND id=? AND kind='campaign'", (workspace_id, run_id)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Kampanjförslaget hittades inte")
        # Serialize submissions for this workspace, including double-clicks and
        # different browser tabs. The queued text always comes from the saved run.
        rows = con.execute("SELECT id,payload_json FROM approvals WHERE workspace_id=? AND action_type='campaign_draft'", (workspace_id,)).fetchall()
        for row in rows:
            if json.loads(row["payload_json"] or "{}").get("source_run_id") == run_id:
                return {"id": row["id"], "created": False}
        data = json.loads(run["input_json"] or "{}")
        title = f"Launch: {data.get('campaign_name') or run['company_name']}"[:180]
        payload = {"source_run_id": run_id, "channel": data.get("channel"), "budget_sek": data.get("budget_sek"), "objective": data.get("objective")}
        approval_id = store._insert_id(con, "INSERT INTO approvals(workspace_id,created_by,action_type,title,description,provider,risk_level,payload_json) VALUES(?,?,'campaign_draft',?,?,?,'high',?)", (workspace_id, user_id, title, run["output_text"], data.get("channel"), json.dumps(payload)))
    store.add_notification(workspace_id, "approval", "Kampanj redo för granskning", title, {"approval_id": approval_id, "source_run_id": run_id})
    return {"id": approval_id, "created": True}


def approval_review(workspace_id: int, approval_id: int) -> dict[str, Any]:
    approval = store.get_approval(workspace_id, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    with store._connect() as con:
        rows = con.execute("SELECT id,status,user_id,created_at FROM execution_log WHERE workspace_id=? AND approval_id=? ORDER BY id", (workspace_id, approval_id)).fetchall()
    # The timeline deliberately exposes no raw provider request/response data.
    timeline = [{"event": "created", "at": approval["created_at"], "user_id": approval.get("created_by")}]
    if approval.get("reviewed_at"):
        timeline.append({"event": "approved" if approval["status"] in {"approved", "executed", "failed"} else "rejected", "at": approval["reviewed_at"], "user_id": approval.get("reviewed_by"), "note": approval.get("review_note") or ""})
    timeline.extend({"event": row["status"], "at": row["created_at"], "user_id": row["user_id"]} for row in rows)
    return {"approval": approval, "timeline": timeline}
