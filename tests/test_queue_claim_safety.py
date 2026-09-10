from pathlib import Path

import app.emailer as emailer
import app.jobs as jobs
import app.store as store
from app.queue_claim_safety import claim_email_atomic, claim_job_atomic


ROOT = Path(__file__).resolve().parents[1]
INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
SOURCE = (ROOT / "app" / "queue_claim_safety.py").read_text(encoding="utf-8")
POSTGRES = (ROOT / "app" / "postgres_compat.py").read_text(encoding="utf-8")


class FakeCursor:
    def __init__(self, row=None, rowcount=0):
        self._row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self._row


class FakeConnection:
    def __init__(self, selected, claimed, after):
        self.selected = selected
        self.claimed = claimed
        self.after = after
        self.calls = []
        self.select_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        normalized = sql.lstrip().upper()
        if normalized.startswith("BEGIN"):
            return FakeCursor(rowcount=0)
        if normalized.startswith("UPDATE"):
            return FakeCursor(rowcount=self.claimed)
        if normalized.startswith("SELECT"):
            self.select_count += 1
            return FakeCursor(row=self.selected if self.select_count == 1 else self.after)
        raise AssertionError(sql)


def _job_claim_sql(connection: FakeConnection) -> str:
    return next(
        sql
        for sql, _ in connection.calls
        if "UPDATE jobs SET status='running'" in sql and "WHERE id=?" in sql
    )


def test_job_claim_returns_only_when_worker_wins_conditional_update(monkeypatch):
    row = {"id": 3, "workspace_id": 1, "kind": "sync_google", "payload_json": '{"days": 30}', "attempts": 1}
    after = {**row, "status": "running", "payload_json": '{"days": 30}', "attempts": 2}
    won = FakeConnection(row, 1, after)
    monkeypatch.setattr(store, "_connect", lambda: won)
    result = claim_job_atomic()
    assert result["id"] == 3
    assert result["payload"] == {"days": 30}
    claim_sql = _job_claim_sql(won)
    assert "status='queued'" in claim_sql
    assert "datetime(run_after)<=CURRENT_TIMESTAMP" in claim_sql

    lost = FakeConnection(row, 0, after)
    monkeypatch.setattr(store, "_connect", lambda: lost)
    assert claim_job_atomic() is None
    assert lost.select_count == 1


def test_email_claim_returns_only_when_worker_wins_conditional_update(monkeypatch):
    row = {"id": 8, "recipient": "pilot@example.com", "subject": "Hej", "body_text": "Text"}
    after = {**row, "status": "sending"}
    won = FakeConnection(row, 1, after)
    monkeypatch.setattr(store, "_connect", lambda: won)
    result = claim_email_atomic()
    assert result["id"] == 8
    assert "status='queued'" in won.calls[2][0]

    lost = FakeConnection(row, 0, after)
    monkeypatch.setattr(store, "_connect", lambda: lost)
    assert claim_email_atomic() is None
    assert lost.select_count == 1


def test_empty_queues_do_not_attempt_item_claim_update(monkeypatch):
    empty_job = FakeConnection(None, 1, None)
    monkeypatch.setattr(store, "_connect", lambda: empty_job)
    assert claim_job_atomic() is None
    assert not any("UPDATE jobs SET status='running'" in sql for sql, _ in empty_job.calls)

    empty_email = FakeConnection(None, 1, None)
    monkeypatch.setattr(store, "_connect", lambda: empty_email)
    assert claim_email_atomic() is None
    assert not any("UPDATE email_outbox SET status='sending'" in sql for sql, _ in empty_email.calls)


def test_worker_and_emailer_bind_atomic_claim_helpers():
    assert INIT.index("install_queue_claim_safety") < INIT.index("from .main import app as _app")
    assert store.claim_job is claim_job_atomic
    assert store.claim_email is claim_email_atomic
    assert jobs.claim_job is claim_job_atomic
    assert emailer.claim_email is claim_email_atomic


def test_postgres_translation_does_not_rely_on_begin_immediate_serialization():
    assert 'if statement.upper() == "BEGIN IMMEDIATE":' in POSTGRES
    assert 'return "BEGIN"' in POSTGRES
    assert "claimed.rowcount != 1" in SOURCE


def test_queue_claim_guard_does_not_execute_jobs_or_send_email_itself():
    for forbidden in (
        "execute_job",
        "send_email",
        "finish_job",
        "finish_email",
        "sync_google",
        "sync_meta",
        "run_autopilot_once",
        "httpx",
        "smtplib",
        "SMTP_PASSWORD",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
    ):
        assert forbidden not in SOURCE
