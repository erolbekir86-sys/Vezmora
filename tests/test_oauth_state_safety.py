from __future__ import annotations

import sqlite3

from app import connectors, oauth_state_safety, postgres_compat, store


def _oauth_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE oauth_states (
            state TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            workspace_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    return con


def test_saving_fresh_state_prunes_only_expired_rows(monkeypatch) -> None:
    con = _oauth_db()
    con.execute(
        """INSERT INTO oauth_states(state,user_id,workspace_id,provider,created_at)
           VALUES(?,?,?,?,datetime('now','-21 minutes'))""",
        ("expired_state", 1, 10, "google"),
    )
    con.execute(
        """INSERT INTO oauth_states(state,user_id,workspace_id,provider,created_at)
           VALUES(?,?,?,?,datetime('now','-5 minutes'))""",
        ("active_state", 2, 20, "meta"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    oauth_state_safety.save_oauth_state_with_cleanup("new_state", 3, 30, "google")

    states = {
        row[0]
        for row in con.execute("SELECT state FROM oauth_states ORDER BY state").fetchall()
    }
    assert states == {"active_state", "new_state"}
    new_row = con.execute(
        "SELECT user_id,workspace_id,provider FROM oauth_states WHERE state='new_state'"
    ).fetchone()
    assert tuple(new_row) == (3, 30, "google")


def test_oauth_state_can_only_be_consumed_once(monkeypatch) -> None:
    con = _oauth_db()
    con.execute(
        "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
        ("safe_state_123", 7, 42, "google"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    first = oauth_state_safety.consume_oauth_state_atomic("safe_state_123", "google")
    second = oauth_state_safety.consume_oauth_state_atomic("safe_state_123", "google")

    assert first is not None
    assert first["user_id"] == 7
    assert first["workspace_id"] == 42
    assert first["provider"] == "google"
    assert second is None
    assert con.execute("SELECT COUNT(*) FROM oauth_states").fetchone()[0] == 0


def test_wrong_provider_does_not_destroy_valid_state(monkeypatch) -> None:
    con = _oauth_db()
    con.execute(
        "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
        ("provider_scoped_state", 8, 43, "meta"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    assert oauth_state_safety.consume_oauth_state_atomic("provider_scoped_state", "google") is None
    valid = oauth_state_safety.consume_oauth_state_atomic("provider_scoped_state", "meta")

    assert valid is not None
    assert valid["provider"] == "meta"


def test_expired_oauth_state_is_not_consumed(monkeypatch) -> None:
    con = _oauth_db()
    con.execute(
        """INSERT INTO oauth_states(state,user_id,workspace_id,provider,created_at)
           VALUES(?,?,?,?,datetime('now','-21 minutes'))""",
        ("expired_state", 9, 44, "google"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    assert oauth_state_safety.consume_oauth_state_atomic("expired_state", "google") is None
    assert con.execute(
        "SELECT COUNT(*) FROM oauth_states WHERE state='expired_state'"
    ).fetchone()[0] == 1


def test_postgres_compat_translates_oauth_expiry_expressions() -> None:
    consume_sql = postgres_compat._sql(
        """DELETE FROM oauth_states
           WHERE state=? AND provider=?
             AND created_at >= datetime('now','-20 minutes')
           RETURNING *"""
    )
    cleanup_sql = postgres_compat._sql(
        "DELETE FROM oauth_states WHERE created_at < datetime('now','-20 minutes')"
    )

    assert "CURRENT_TIMESTAMP - INTERVAL '20 minutes'" in consume_sql
    assert consume_sql.count("%s") == 2
    assert "RETURNING *" in consume_sql
    assert "CURRENT_TIMESTAMP - INTERVAL '20 minutes'" in cleanup_sql


def test_oauth_state_helpers_are_installed_before_connectors_bind_them() -> None:
    assert getattr(store, "_vexmera_oauth_state_safety_installed", False) is True
    assert store.save_oauth_state is oauth_state_safety.save_oauth_state_with_cleanup
    assert store.consume_oauth_state is oauth_state_safety.consume_oauth_state_atomic
    assert connectors.save_oauth_state is oauth_state_safety.save_oauth_state_with_cleanup
    assert connectors.consume_oauth_state is oauth_state_safety.consume_oauth_state_atomic
