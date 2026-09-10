from __future__ import annotations

from datetime import datetime, timedelta, timezone

import app.auth as auth
import app.main as main_module
import app.store as store
from app import capability_retention


def _prepare_db(tmp_path, monkeypatch) -> tuple[int, int]:
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "capability-retention.db")
    store.init_db()
    return store.create_user("retention@example.com", "salt", "hash", "Retention")


def _iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).isoformat()


def test_new_session_prunes_only_expired_sessions(tmp_path, monkeypatch) -> None:
    user_id, _ = _prepare_db(tmp_path, monkeypatch)
    with store._connect() as con:
        con.execute(
            "INSERT INTO sessions(user_id,token_hash,expires_at) VALUES(?,?,?)",
            (user_id, "expired-session", _iso(timedelta(minutes=-5))),
        )
        con.execute(
            "INSERT INTO sessions(user_id,token_hash,expires_at) VALUES(?,?,?)",
            (user_id, "active-session", _iso(timedelta(hours=1))),
        )

    capability_retention.create_session_with_retention(user_id, "new-session", _iso(timedelta(hours=2)))

    with store._connect() as con:
        rows = con.execute("SELECT token_hash FROM sessions ORDER BY token_hash").fetchall()
    assert [row["token_hash"] for row in rows] == ["active-session", "new-session"]


def test_new_password_reset_prunes_expired_reset_rows(tmp_path, monkeypatch) -> None:
    user_id, _ = _prepare_db(tmp_path, monkeypatch)
    with store._connect() as con:
        con.execute(
            "INSERT INTO password_reset_tokens(user_id,token_hash,expires_at,used_at) VALUES(?,?,?,CURRENT_TIMESTAMP)",
            (user_id, "expired-reset", _iso(timedelta(minutes=-5))),
        )

    new_id = capability_retention.create_password_reset_with_retention(
        user_id,
        "new-reset",
        _iso(timedelta(hours=1)),
    )

    with store._connect() as con:
        expired = con.execute(
            "SELECT COUNT(*) FROM password_reset_tokens WHERE token_hash='expired-reset'"
        ).fetchone()[0]
        fresh = con.execute("SELECT token_hash FROM password_reset_tokens WHERE id=?", (new_id,)).fetchone()
    assert expired == 0
    assert fresh["token_hash"] == "new-reset"


def test_new_workspace_invite_prunes_expired_invites_but_keeps_active(tmp_path, monkeypatch) -> None:
    user_id, workspace_id = _prepare_db(tmp_path, monkeypatch)
    with store._connect() as con:
        con.execute(
            "INSERT INTO workspace_invites(workspace_id,email,role,token_hash,invited_by,expires_at) VALUES(?,?,?,?,?,?)",
            (workspace_id, "old@example.com", "marketer", "expired-invite", user_id, _iso(timedelta(minutes=-5))),
        )
        con.execute(
            "INSERT INTO workspace_invites(workspace_id,email,role,token_hash,invited_by,expires_at) VALUES(?,?,?,?,?,?)",
            (workspace_id, "active@example.com", "viewer", "active-invite", user_id, _iso(timedelta(days=1))),
        )

    new_id = capability_retention.create_workspace_invite_with_retention(
        workspace_id,
        "new@example.com",
        "marketer",
        "new-invite",
        user_id,
        _iso(timedelta(days=7)),
    )

    with store._connect() as con:
        hashes = {
            row["token_hash"]
            for row in con.execute("SELECT token_hash FROM workspace_invites").fetchall()
        }
        new_row = con.execute("SELECT id FROM workspace_invites WHERE token_hash='new-invite'").fetchone()
    assert hashes == {"active-invite", "new-invite"}
    assert new_row["id"] == new_id


def test_retention_table_name_is_fixed_allowlist() -> None:
    try:
        capability_retention._prune_expired("users")
    except ValueError as exc:
        assert "Unsupported capability table" in str(exc)
    else:
        raise AssertionError("Dynamic table names outside the capability allowlist must be rejected")


def test_auth_and_main_bind_retention_wrappers() -> None:
    assert getattr(store, "_vexmera_capability_retention_installed", False) is True
    assert store.create_session is capability_retention.create_session_with_retention
    assert auth.create_session is capability_retention.create_session_with_retention
    assert store.create_password_reset is capability_retention.create_password_reset_with_retention
    assert main_module.create_password_reset is capability_retention.create_password_reset_with_retention
    assert store.create_workspace_invite is capability_retention.create_workspace_invite_with_retention
    assert main_module.create_workspace_invite is capability_retention.create_workspace_invite_with_retention
