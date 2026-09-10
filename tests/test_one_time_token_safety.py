from pathlib import Path

import app.main as app_main
import app.store as store
from app.one_time_token_safety import (
    consume_password_reset_atomic,
    consume_workspace_invite_atomic,
)


ROOT = Path(__file__).resolve().parents[1]
INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
SOURCE = (ROOT / "app" / "one_time_token_safety.py").read_text(encoding="utf-8")


class FakeCursor:
    def __init__(self, row=None, rowcount=0):
        self._row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self._row


class FakeConnection:
    def __init__(self, row, claim_rowcount):
        self.row = row
        self.claim_rowcount = claim_rowcount
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if sql.lstrip().upper().startswith("SELECT"):
            return FakeCursor(row=self.row)
        return FakeCursor(rowcount=self.claim_rowcount)


def test_workspace_invite_returns_only_when_conditional_claim_wins(monkeypatch):
    row = {"id": 7, "workspace_id": 2, "email": "pilot@example.com", "role": "marketer"}
    won = FakeConnection(row, 1)
    monkeypatch.setattr(store, "_connect", lambda: won)
    result = consume_workspace_invite_atomic("hash", "pilot@example.com")
    assert result == row
    assert "accepted_at IS NULL AND expires_at>?" in won.calls[1][0]

    lost = FakeConnection(row, 0)
    monkeypatch.setattr(store, "_connect", lambda: lost)
    assert consume_workspace_invite_atomic("hash", "pilot@example.com") is None


def test_password_reset_returns_user_only_when_conditional_claim_wins(monkeypatch):
    row = {"id": 9, "user_id": 42}
    won = FakeConnection(row, 1)
    monkeypatch.setattr(store, "_connect", lambda: won)
    assert consume_password_reset_atomic("hash") == 42
    assert "used_at IS NULL AND expires_at>?" in won.calls[1][0]

    lost = FakeConnection(row, 0)
    monkeypatch.setattr(store, "_connect", lambda: lost)
    assert consume_password_reset_atomic("hash") is None


def test_missing_or_expired_token_never_attempts_claim(monkeypatch):
    missing = FakeConnection(None, 1)
    monkeypatch.setattr(store, "_connect", lambda: missing)
    assert consume_password_reset_atomic("missing") is None
    assert len(missing.calls) == 1

    missing_invite = FakeConnection(None, 1)
    monkeypatch.setattr(store, "_connect", lambda: missing_invite)
    assert consume_workspace_invite_atomic("missing", "nobody@example.com") is None
    assert len(missing_invite.calls) == 1


def test_guard_is_installed_before_main_binds_store_helpers():
    assert INIT.index("install_one_time_token_safety") < INIT.index("from .main import app as _app")
    assert app_main.consume_password_reset is store.consume_password_reset
    assert app_main.consume_workspace_invite is store.consume_workspace_invite
    assert store.consume_password_reset is consume_password_reset_atomic
    assert store.consume_workspace_invite is consume_workspace_invite_atomic


def test_atomic_guard_uses_rowcount_and_does_not_handle_raw_tokens_or_secrets():
    assert "claimed.rowcount != 1" in SOURCE
    assert "token_hash" in SOURCE
    assert "raw_token" not in SOURCE
    for forbidden in (
        "GOOGLE_CLIENT_SECRET",
        "META_APP_SECRET",
        "STRIPE_SECRET_KEY",
        "httpx",
        "requests",
        "queue_email",
    ):
        assert forbidden not in SOURCE
