from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from app import queue_claim_safety


def _job_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'queued',
            run_after TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            locked_at TEXT,
            finished_at TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            error_text TEXT
        )"""
    )
    return con


def _insert_running(con: sqlite3.Connection, *, attempts: int, age_minutes: int, kind: str = "sync_google") -> int:
    locked_at = (datetime.now(timezone.utc) - timedelta(minutes=age_minutes)).isoformat()
    cur = con.execute(
        """INSERT INTO jobs(workspace_id,kind,payload_json,status,locked_at,attempts)
           VALUES(1,?,?, 'running',?,?)""",
        (kind, '{"days":7}', locked_at, attempts),
    )
    con.commit()
    return int(cur.lastrowid)


def test_retryable_stale_job_is_requeued(monkeypatch) -> None:
    con = _job_db()
    job_id = _insert_running(con, attempts=1, age_minutes=31)
    monkeypatch.delenv("VEZMORA_JOB_STALE_MINUTES", raising=False)

    queue_claim_safety._recover_stale_jobs(con)
    row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()

    assert row["status"] == "queued"
    assert row["locked_at"] is None
    assert row["attempts"] == 1
    assert "Recovered stale worker lock after 30 minutes" == row["error_text"]


def test_stale_job_at_retry_limit_is_failed(monkeypatch) -> None:
    con = _job_db()
    job_id = _insert_running(con, attempts=3, age_minutes=31)
    monkeypatch.delenv("VEZMORA_JOB_STALE_MINUTES", raising=False)

    queue_claim_safety._recover_stale_jobs(con)
    row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()

    assert row["status"] == "failed"
    assert row["finished_at"] is not None
    assert row["attempts"] == 3
    assert row["error_text"] == "Worker lock expired after retry budget"


def test_fresh_running_job_is_never_recovered(monkeypatch) -> None:
    con = _job_db()
    job_id = _insert_running(con, attempts=1, age_minutes=5)
    monkeypatch.delenv("VEZMORA_JOB_STALE_MINUTES", raising=False)

    queue_claim_safety._recover_stale_jobs(con)
    row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()

    assert row["status"] == "running"
    assert row["locked_at"] is not None
    assert row["error_text"] is None


def test_claim_can_resume_retryable_stale_job_once(monkeypatch) -> None:
    con = _job_db()
    job_id = _insert_running(con, attempts=1, age_minutes=31)
    monkeypatch.delenv("VEZMORA_JOB_STALE_MINUTES", raising=False)
    monkeypatch.setattr(queue_claim_safety._store, "_connect", lambda: con)

    job = queue_claim_safety.claim_job_atomic()

    assert job is not None
    assert job["id"] == job_id
    assert job["status"] == "running"
    assert job["attempts"] == 2
    assert job["payload"] == {"days": 7}


def test_stale_threshold_is_bounded_and_invalid_values_fail_safe(monkeypatch) -> None:
    monkeypatch.setenv("VEZMORA_JOB_STALE_MINUTES", "not-a-number")
    assert queue_claim_safety._stale_job_minutes() == 30

    monkeypatch.setenv("VEZMORA_JOB_STALE_MINUTES", "1")
    assert queue_claim_safety._stale_job_minutes() == 10

    monkeypatch.setenv("VEZMORA_JOB_STALE_MINUTES", "99999")
    assert queue_claim_safety._stale_job_minutes() == 1440
