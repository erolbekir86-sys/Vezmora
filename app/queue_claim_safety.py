from __future__ import annotations

import json
from typing import Any

from . import store as _store


def claim_job_atomic() -> dict[str, Any] | None:
    """Claim one queued job only when this worker wins the conditional update."""
    with _store._connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT * FROM jobs WHERE status='queued' AND datetime(run_after)<=CURRENT_TIMESTAMP ORDER BY id LIMIT 1"
        ).fetchone()
        if not row:
            return None

        claimed = con.execute(
            "UPDATE jobs SET status='running',locked_at=CURRENT_TIMESTAMP,attempts=attempts+1 "
            "WHERE id=? AND status='queued' AND datetime(run_after)<=CURRENT_TIMESTAMP",
            (row["id"],),
        )
        if claimed.rowcount != 1:
            return None

        got = con.execute("SELECT * FROM jobs WHERE id=? AND status='running'", (row["id"],)).fetchone()
        if not got:
            return None

    data = dict(got)
    try:
        data["payload"] = json.loads(data.pop("payload_json") or "{}")
    except (TypeError, json.JSONDecodeError):
        data["payload"] = {}
    return data


def claim_email_atomic() -> dict[str, Any] | None:
    """Claim one queued email only when this worker wins the conditional update."""
    with _store._connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT * FROM email_outbox WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        if not row:
            return None

        claimed = con.execute(
            "UPDATE email_outbox SET status='sending' WHERE id=? AND status='queued'",
            (row["id"],),
        )
        if claimed.rowcount != 1:
            return None

        got = con.execute("SELECT * FROM email_outbox WHERE id=? AND status='sending'", (row["id"],)).fetchone()
        return dict(got) if got else None


def install_queue_claim_safety() -> None:
    """Install atomic queue claims before jobs/emailer bind store helpers."""
    if getattr(_store, "_vexmera_queue_claim_safety_installed", False):
        return

    _store.claim_job = claim_job_atomic
    _store.claim_email = claim_email_atomic
    _store._vexmera_queue_claim_safety_installed = True
