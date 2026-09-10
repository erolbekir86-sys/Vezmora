from __future__ import annotations

import app.emailer as emailer
import app.store as store
from app import email_outbox_privacy


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str, params=()):
        self.calls.append((sql, tuple(params)))
        return object()


def test_successful_email_body_is_scrubbed_after_original_finish(monkeypatch) -> None:
    events: list[tuple] = []
    con = FakeConnection()

    def fake_original(email_id: int, error: str | None = None) -> None:
        events.append(("finish", email_id, error))

    monkeypatch.setattr(email_outbox_privacy, "_ORIGINAL_FINISH_EMAIL", fake_original)
    monkeypatch.setattr(email_outbox_privacy._store, "_connect", lambda: con)

    email_outbox_privacy.finish_email_with_body_scrub(17)

    assert events == [("finish", 17, None)]
    assert len(con.calls) == 1
    sql, params = con.calls[0]
    assert "SET body_text=''" in sql
    assert "status='sent'" in sql
    assert params == (17,)


def test_failed_email_keeps_body_available_for_future_retry(monkeypatch) -> None:
    events: list[tuple] = []

    def fake_original(email_id: int, error: str | None = None) -> None:
        events.append(("finish", email_id, error))

    monkeypatch.setattr(email_outbox_privacy, "_ORIGINAL_FINISH_EMAIL", fake_original)

    def should_not_connect():
        raise AssertionError("Failed email body must not be scrubbed")

    monkeypatch.setattr(email_outbox_privacy._store, "_connect", should_not_connect)

    email_outbox_privacy.finish_email_with_body_scrub(18, "SMTP timeout")

    assert events == [("finish", 18, "SMTP timeout")]


def test_scrub_update_is_status_guarded() -> None:
    source = open(email_outbox_privacy.__file__, encoding="utf-8").read()
    assert "WHERE id=? AND status='sent'" in source
    assert "if error:" in source


def test_emailer_binds_privacy_wrapped_finish_helper() -> None:
    assert getattr(store, "_vexmera_email_outbox_privacy_installed", False) is True
    assert store.finish_email is email_outbox_privacy.finish_email_with_body_scrub
    assert emailer.finish_email is email_outbox_privacy.finish_email_with_body_scrub
