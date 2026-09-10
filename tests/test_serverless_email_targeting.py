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


def test_stale_reset_is_failed_and_scrubbed_before_next_mail_is_claimed(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "stale-reset.db")
    reset_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(
        None,
        "reset@example.test",
        queue_claim_safety._RESET_EMAIL_SUBJECT,
        "https://example.test/app?reset=secret-reset-token",
    )
    normal_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(None, "normal@example.test", "Normal mail", "hello")
    with store._connect() as con:
        con.execute("UPDATE email_outbox SET created_at='2000-01-01 00:00:00' WHERE id=?", (reset_id,))

    claimed = queue_claim_safety.claim_email_atomic()

    assert claimed is not None
    assert claimed["id"] == normal_id
    with store._connect() as con:
        stale = con.execute(
            "SELECT status,error_text,body_text FROM email_outbox WHERE id=?",
            (reset_id,),
        ).fetchone()
    assert stale["status"] == "failed"
    assert stale["error_text"] == queue_claim_safety._STALE_CAPABILITY_ERROR
    assert stale["body_text"] == ""


def test_fresh_reset_email_remains_deliverable(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "fresh-reset.db")
    reset_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(
        None,
        "reset@example.test",
        queue_claim_safety._RESET_EMAIL_SUBJECT,
        "fresh reset body",
    )

    claimed = queue_claim_safety.claim_email_atomic()

    assert claimed is not None
    assert claimed["id"] == reset_id
    assert claimed["status"] == "sending"


def test_stale_invite_is_failed_and_scrubbed(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "stale-invite.db")
    invite_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(
        None,
        "invite@example.test",
        queue_claim_safety._INVITE_EMAIL_SUBJECT,
        "https://example.test/app?invite=secret-invite-token",
    )
    with store._connect() as con:
        con.execute("UPDATE email_outbox SET created_at='2000-01-01 00:00:00' WHERE id=?", (invite_id,))

    assert queue_claim_safety.claim_email_atomic() is None
    with store._connect() as con:
        stale = con.execute(
            "SELECT status,error_text,body_text FROM email_outbox WHERE id=?",
            (invite_id,),
        ).fetchone()
    assert stale["status"] == "failed"
    assert stale["error_text"] == queue_claim_safety._STALE_CAPABILITY_ERROR
    assert stale["body_text"] == ""


def test_stale_failed_capability_body_is_scrubbed_without_requeue(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "stale-failed.db")
    reset_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(
        None,
        "reset@example.test",
        queue_claim_safety._RESET_EMAIL_SUBJECT,
        "sensitive reset body",
    )
    with store._connect() as con:
        con.execute(
            "UPDATE email_outbox SET status='failed',error_text='temporary smtp error',created_at='2000-01-01 00:00:00' WHERE id=?",
            (reset_id,),
        )

    assert queue_claim_safety.claim_email_atomic() is None
    with store._connect() as con:
        stale = con.execute(
            "SELECT status,error_text,body_text FROM email_outbox WHERE id=?",
            (reset_id,),
        ).fetchone()
    assert stale["status"] == "failed"
    assert stale["error_text"] == "temporary smtp error"
    assert stale["body_text"] == ""


def test_old_non_capability_mail_is_still_claimable(tmp_path, monkeypatch) -> None:
    _prepare_db(tmp_path, monkeypatch, "old-normal.db")
    mail_id = queue_claim_safety._ORIGINAL_QUEUE_EMAIL(None, "old@example.test", "Normal mail", "still useful")
    with store._connect() as con:
        con.execute("UPDATE email_outbox SET created_at='2000-01-01 00:00:00' WHERE id=?", (mail_id,))

    claimed = queue_claim_safety.claim_email_atomic()

    assert claimed is not None
    assert claimed["id"] == mail_id
    assert claimed["body_text"] == "still useful"


def test_queue_and_emailer_bind_targeted_atomic_helpers() -> None:
    assert store.queue_email is queue_claim_safety.queue_email_with_inline_target
    assert store.claim_email is queue_claim_safety.claim_email_atomic
    assert main_module.queue_email is queue_claim_safety.queue_email_with_inline_target
    assert emailer.claim_email is queue_claim_safety.claim_email_atomic
