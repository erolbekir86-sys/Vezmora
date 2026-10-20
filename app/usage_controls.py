"""Workspace-wide AI run reservations, shared by UI, workers and scheduler.

A run is a capacity unit, not a token estimate or a currency charge. Reserve
before calling a model so concurrent/background calls cannot bypass the cap.
Interrupted processes keep their reservation; known failures release it.
"""
from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from fastapi import HTTPException

from . import store
from .billing import _stored_plan, _trial_active
from .pricing import PLANS

T = TypeVar("T")


def _locked_settings(con: Any, workspace_id: int) -> dict[str, Any]:
    con.execute("BEGIN IMMEDIATE")
    con.execute("INSERT OR IGNORE INTO workspace_settings(workspace_id) VALUES(?)", (workspace_id,))
    # BEGIN IMMEDIATE serializes SQLite. This UPDATE also takes a row lock on
    # PostgreSQL, where the compatibility layer maps BEGIN IMMEDIATE to BEGIN.
    con.execute("UPDATE workspace_settings SET updated_at=updated_at WHERE workspace_id=?", (workspace_id,))
    return dict(con.execute("SELECT * FROM workspace_settings WHERE workspace_id=?", (workspace_id,)).fetchone())


def capacity(settings: dict[str, Any]) -> tuple[int, int]:
    included = int(PLANS[_stored_plan(settings.get("plan"))]["ai_runs"])
    chosen = settings.get("ai_monthly_run_limit")
    return included, min(included, max(0, int(chosen))) if chosen is not None else included


def set_monthly_limit(workspace_id: int, limit: int | None) -> None:
    with store._connect() as con:
        _locked_settings(con, workspace_id)
        con.execute("UPDATE workspace_settings SET ai_monthly_run_limit=?,updated_at=CURRENT_TIMESTAMP WHERE workspace_id=?", (limit, workspace_id))


def reserve_run(workspace_id: int, kind: str, source: str) -> int:
    with store._connect() as con:
        settings = _locked_settings(con, workspace_id)
        if settings.get("billing_status") in {"canceled", "unpaid", "incomplete_expired"} and not _trial_active(settings):
            raise HTTPException(status_code=402, detail="An active Vexmera subscription is required")
        _, limit = capacity(settings)
        used = con.execute("SELECT COALESCE(SUM(units),0) AS used FROM usage_events WHERE workspace_id=? AND kind='ai_runs' AND created_at>=datetime('now','start of month')", (workspace_id,)).fetchone()["used"]
        if int(used) >= limit:
            raise HTTPException(status_code=402, detail="Månadsgränsen för AI-körningar är nådd. En ägare eller administratör kan ändra gränsen inom planens kapacitet.")
        return store._insert_id(con, "INSERT INTO usage_events(workspace_id,kind,units,metadata_json) VALUES(?,'ai_runs',1,?)", (workspace_id, json.dumps({"kind": kind, "source": source, "state": "reserved"})))


async def run_metered(workspace_id: int, kind: str, generate: Callable[[], Awaitable[T]], *, source: str = "manual") -> T:
    reservation = reserve_run(workspace_id, kind, source)
    try:
        output = await generate()
    except BaseException:
        with store._connect() as con:
            con.execute("DELETE FROM usage_events WHERE id=? AND workspace_id=? AND kind='ai_runs'", (reservation, workspace_id))
        raise
    with store._connect() as con:
        con.execute("UPDATE usage_events SET metadata_json=? WHERE id=? AND workspace_id=?", (json.dumps({"kind": kind, "source": source, "state": "completed"}), reservation, workspace_id))
    return output


def usage_overview(workspace_id: int) -> dict[str, Any]:
    settings = store.get_workspace_settings(workspace_id)
    included, limit = capacity(settings)
    with store._connect() as con:
        rows = con.execute("SELECT id,units,metadata_json,created_at FROM usage_events WHERE workspace_id=? AND kind='ai_runs' AND created_at>=datetime('now','start of month') ORDER BY id DESC", (workspace_id,)).fetchall()
    used = sum(int(row["units"]) for row in rows)
    by_kind: dict[str, int] = {}
    by_source: dict[str, int] = {}
    recent = []
    for row in rows:
        metadata = json.loads(row["metadata_json"] or "{}")
        kind, source = str(metadata.get("kind") or "other"), str(metadata.get("source") or "manual")
        by_kind[kind] = by_kind.get(kind, 0) + int(row["units"])
        by_source[source] = by_source.get(source, 0) + int(row["units"])
        if len(recent) < 20:
            recent.append({"id": row["id"], "kind": kind, "source": source, "units": row["units"], "state": metadata.get("state") or "completed", "created_at": row["created_at"]})
    return {"unit": "ai_runs", "period": "calendar_month_utc", "included": included,
            "monthly_limit": settings.get("ai_monthly_run_limit"), "effective_limit": limit,
            "used": used, "remaining": max(0, limit-used), "blocked": used >= limit,
            "warning": used >= limit * 0.8, "by_kind": by_kind, "by_source": by_source,
            "recent": recent, "automatic_overage": False}
