from __future__ import annotations

from fastapi.testclient import TestClient

import app.emailer as emailer
import app.main as main_module
import app.store as store
from app import queue_claim_safety


def _prepare_db(tmp_path, monkeypatch, name: str) -> None:
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / name)
    queue_claim_safety._INLINE_EMAIL_TARGETS.set(())
    store.init_db()


def _enable_inline_mail(monkeypatch) -> None:
    monkeypatch.setenv("VEZMORA_SERVERLESS", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.test")


def test_serverless_inline_claim_targets_new_mail_ahead_of_older_queue(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "targeted-email.db")
    _enable_inline_mail(monkeypatch)

    older_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(None, "old@example.test", "Old", "old body")
    target_id = queue_claim_safety.queue_email_with_inline_target(
        None,
        "reset@example.test",
        "Reset",
        "new reset body",
    )

    claimed = queue_claim_safety.claim_email_atomic()

    assert claimed is not None
    assert claimed["id"] == target_id
    assert claimed["recipient"] == "reset@example.test"
    with store._connect() as con:
        older = con.execute("SELECT status FROM email_outbox WHERE id=?", (older_id,)).fetchone()
        target = con.execute("SELECT status FROM email_outbox WHERE id=?", (target_id,)).fetchone()
    assert older["status"] == "queued"
    assert target["status"] == "sending"


def test_unavailable_inline_target_does_not_fall_through_to_unrelated_mail(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "target-race.db")
    _enable_inline_mail(monkeypatch)

    older_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(None, "old@example.test", "Old", "old body")
    target_id = queue_claim_safety.queue_email_with_inline_target(None, "new@example.test", "New", "new body")
    with store._connect() as con:
        con.execute("UPDATE email_outbox SET status='sending' WHERE id=?", (target_id,))

    assert queue_claim_safety.claim_email_atomic() is None
    with store._connect() as con:
        older = con.execute("SELECT status FROM email_outbox WHERE id=?", (older_id,)).fetchone()
    assert older["status"] == "queued"


def test_non_serverless_claim_keeps_existing_fifo_behavior(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "fifo-email.db")
    monkeypatch.setenv("VEZMORA_SERVERLESS", "false")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.test")

    older_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(None, "old@example.test", "Old", "old body")
    queue_claim_safety.queue_email_with_inline_target(None, "new@example.test", "New", "new body")

    claimed = queue_claim_safety.claim_email_atomic()
    assert claimed is not None
    assert claimed["id"] == older_id


def test_password_reset_inline_send_delivers_the_reset_not_an_older_message(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "reset-route.db")
    _enable_inline_mail(monkeypatch)
    monkeypatch.setenv("VEZMORA_DEV_SHOW_TOKENS", "true")
    delivered: list[tuple[str, str]] = []
    monkeypatch.setattr(emailer, "send_email", lambda recipient, subject, body: delivered.append((recipient, subject)))

    with TestClient(main_module.app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"email": "reset-target@example.com", "password": "verysecure123", "workspace_name": "Reset target"},
        )
        assert registered.status_code == 200
        client.post("/api/auth/logout")

        older_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(None, "older@example.test", "Old queued mail", "old")
        reset = client.post(
            "/api/auth/password-reset/request",
            json={"email": "reset-target@example.com"},
        )

        assert reset.status_code == 200
        assert delivered == [("reset-target@example.com", "Reset your Vexmera password")]
        with store._connect() as con:
            older = con.execute("SELECT status FROM email_outbox WHERE id=?", (older_id,)).fetchone()
            reset_row = con.execute(
                "SELECT status,body_text FROM email_outbox WHERE recipient=? ORDER BY id DESC LIMIT 1",
                ("reset-target@example.com",),
            ).fetchone()
        assert older["status"] == "queued"
        assert reset_row["status"] == "sent"
        assert reset_row["body_text"] == ""


def test_queue_and_emailer_bind_targeted_atomic_helpers() -> None:
    assert store.queue_email is queue_claim_safety.queue_email_with_inline_target
    assert store.claim_email is queue_claim_safety.claim_email_atomic
    assert main_module.queue_email is queue_claim_safety.queue_email_with_inline_target
    assert emailer.claim_email is queue_claim_safety.claim_email_atomic
