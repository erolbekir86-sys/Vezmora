from __future__ import annotations

import hashlib
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


def test_saving_fresh_state_prunes_only_expired_rows_and_hashes_new_state(monkeypatch) -> None:
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

    hashed = hashlib.sha256(b"new_state").hexdigest()
    states = {
        row[0]
        for row in con.execute("SELECT state FROM oauth_states ORDER BY state").fetchall()
    }
    assert states == {"active_state", hashed}
    assert "new_state" not in states
    new_row = con.execute(
        "SELECT user_id,workspace_id,provider FROM oauth_states WHERE state=?",
        (hashed,),
    ).fetchone()
    assert tuple(new_row) == (3, 30, "google")


def test_hashed_oauth_state_can_only_be_consumed_once(monkeypatch) -> None:
    con = _oauth_db()
    raw_state = "safe_state_123"
    stored_state = hashlib.sha256(raw_state.encode()).hexdigest()
    con.execute(
        "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
        (stored_state, 7, 42, "google"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    first = oauth_state_safety.consume_oauth_state_atomic(raw_state, "google")
    second = oauth_state_safety.consume_oauth_state_atomic(raw_state, "google")

    assert first is not None
    assert first["user_id"] == 7
    assert first["workspace_id"] == 42
    assert first["provider"] == "google"
    assert second is None
    assert con.execute("SELECT COUNT(*) FROM oauth_states").fetchone()[0] == 0


def test_legacy_raw_oauth_state_remains_consumable_during_rollout(monkeypatch) -> None:
    con = _oauth_db()
    con.execute(
        "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
        ("legacy_raw_state", 6, 41, "google"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    row = oauth_state_safety.consume_oauth_state_atomic("legacy_raw_state", "google")

    assert row is not None
    assert row["user_id"] == 6
    assert con.execute("SELECT COUNT(*) FROM oauth_states").fetchone()[0] == 0


def test_wrong_provider_does_not_destroy_valid_hashed_state(monkeypatch) -> None:
    con = _oauth_db()
    raw_state = "provider_scoped_state"
    stored_state = hashlib.sha256(raw_state.encode()).hexdigest()
    con.execute(
        "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
        (stored_state, 8, 43, "meta"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    assert oauth_state_safety.consume_oauth_state_atomic(raw_state, "google") is None
    valid = oauth_state_safety.consume_oauth_state_atomic(raw_state, "meta")

    assert valid is not None
    assert valid["provider"] == "meta"


def test_expired_oauth_state_is_not_consumed(monkeypatch) -> None:
    con = _oauth_db()
    raw_state = "expired_state"
    stored_state = hashlib.sha256(raw_state.encode()).hexdigest()
    con.execute(
        """INSERT INTO oauth_states(state,user_id,workspace_id,provider,created_at)
           VALUES(?,?,?,?,datetime('now','-21 minutes'))""",
        (stored_state, 9, 44, "google"),
    )
    con.commit()
    monkeypatch.setattr(oauth_state_safety._store, "_connect", lambda: con)

    assert oauth_state_safety.consume_oauth_state_atomic(raw_state, "google") is None
    assert con.execute(
        "SELECT COUNT(*) FROM oauth_states WHERE state=?",
        (stored_state,),
    ).fetchone()[0] == 1


def test_postgres_compat_translates_oauth_expiry_expressions() -> None:
    consume_sql = postgres_compat._sql(
        """DELETE FROM oauth_states
           WHERE (state=? OR state=?) AND provider=?
             AND created_at >= datetime('now','-20 minutes')
           RETURNING *"""
    )
    cleanup_sql = postgres_compat._sql(
        "DELETE FROM oauth_states WHERE created_at < datetime('now','-20 minutes')"
    )

    assert "CURRENT_TIMESTAMP - INTERVAL '20 minutes'" in consume_sql
    assert consume_sql.count("%s") == 3
    assert "RETURNING *" in consume_sql
    assert "CURRENT_TIMESTAMP - INTERVAL '20 minutes'" in cleanup_sql


def test_oauth_state_helpers_are_installed_before_connectors_bind_them() -> None:
    assert getattr(store, "_vexmera_oauth_state_safety_installed", False) is True
    assert store.save_oauth_state is oauth_state_safety.save_oauth_state_with_cleanup
    assert store.consume_oauth_state is oauth_state_safety.consume_oauth_state_atomic
    assert connectors.save_oauth_state is oauth_state_safety.save_oauth_state_with_cleanup
    assert connectors.consume_oauth_state is oauth_state_safety.consume_oauth_state_atomic
