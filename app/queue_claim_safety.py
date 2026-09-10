from __future__ import annotations

import json
import os
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from typing import Any

from . import store as _store

_DEFAULT_STALE_JOB_MINUTES = 30
_MIN_STALE_JOB_MINUTES = 10
_MAX_STALE_JOB_MINUTES = 24 * 60
_MAX_JOB_ATTEMPTS = 3
_ORIGINAL_QUEUE_EMAIL = _store.queue_email
_INLINE_EMAIL_TARGETS: ContextVar[tuple[int, ...]] = ContextVar("vexmera_inline_email_targets", default=())


def _stale_job_minutes() -> int:
    raw = (os.getenv("VEZMORA_JOB_STALE_MINUTES") or "").strip()
    try:
        configured = int(raw) if raw else _DEFAULT_STALE_JOB_MINUTES
    except ValueError:
        configured = _DEFAULT_STALE_JOB_MINUTES
    return max(_MIN_STALE_JOB_MINUTES, min(configured, _MAX_STALE_JOB_MINUTES))


def _recover_stale_jobs(con: Any) -> None:
    """Recover abandoned running jobs without touching recently claimed work."""
    stale_minutes = _stale_job_minutes()
    stale_before = (datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)).isoformat()

    con.execute(
        "UPDATE jobs SET status='queued',run_after=CURRENT_TIMESTAMP,locked_at=NULL,error_text=? "
        "WHERE status='running' AND locked_at IS NOT NULL AND locked_at<? AND attempts<?",
        (f"Recovered stale worker lock after {stale_minutes} minutes", stale_before, _MAX_JOB_ATTEMPTS),
    )
    con.execute(
        "UPDATE jobs SET status='failed',finished_at=CURRENT_TIMESTAMP,error_text=? "
        "WHERE status='running' AND locked_at IS NOT NULL AND locked_at<? AND attempts>=?",
        ("Worker lock expired after retry budget", stale_before, _MAX_JOB_ATTEMPTS),
    )


def claim_job_atomic() -> dict[str, Any] | None:
    """Recover abandoned work, then claim one queued job only if this worker wins."""
    with _store._connect() as con:
        con.execute("BEGIN IMMEDIATE")
        _recover_stale_jobs(con)
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


def _inline_email_delivery_expected() -> bool:
    serverless = (os.getenv("VEZMORA_SERVERLESS") or "").lower() in {"1", "true", "yes", "on"}
    return serverless and bool((os.getenv("SMTP_HOST") or "").strip()) and bool((os.getenv("SMTP_FROM") or "").strip())


def queue_email_with_inline_target(
    workspace_id: int | None,
    recipient: str,
    subject: str,
    body_text: str,
) -> int:
    """Remember newly queued serverless mail so the route's inline send claims that row."""
    email_id = _ORIGINAL_QUEUE_EMAIL(workspace_id, recipient, subject, body_text)
    if _inline_email_delivery_expected():
        targets = _INLINE_EMAIL_TARGETS.get()
        _INLINE_EMAIL_TARGETS.set((*targets, email_id))
    return email_id


def _pop_inline_email_target() -> int | None:
    targets = _INLINE_EMAIL_TARGETS.get()
    if not targets:
        return None
    _INLINE_EMAIL_TARGETS.set(targets[1:])
    return int(targets[0])


def claim_email_atomic() -> dict[str, Any] | None:
    """Claim targeted inline mail when present, otherwise preserve FIFO queue behavior."""
    target_id = _pop_inline_email_target()
    with _store._connect() as con:
        con.execute("BEGIN IMMEDIATE")
        if target_id is None:
            row = con.execute("SELECT * FROM email_outbox WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        else:
            row = con.execute(
                "SELECT * FROM email_outbox WHERE id=? AND status='queued'",
                (target_id,),
            ).fetchone()
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
    """Install atomic queue claims and targeted serverless email delivery before callers bind helpers."""
    if getattr(_store, "_vexmera_queue_claim_safety_installed", False):
        return

    _store.claim_job = claim_job_atomic
    _store.claim_email = claim_email_atomic
    _store.queue_email = queue_email_with_inline_target
    _store._vexmera_queue_claim_safety_installed = True
