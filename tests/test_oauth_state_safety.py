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


def test_postgres_compat_translates_oauth_expiry_expression() -> None:
    translated = postgres_compat._sql(
        """DELETE FROM oauth_states
           WHERE state=? AND provider=?
             AND created_at >= datetime('now','-20 minutes')
           RETURNING *"""
    )

    assert "CURRENT_TIMESTAMP - INTERVAL '20 minutes'" in translated
    assert translated.count("%s") == 2
    assert "RETURNING *" in translated


def test_atomic_oauth_state_helper_is_installed_before_connectors_bind_it() -> None:
    assert getattr(store, "_vexmera_oauth_state_safety_installed", False) is True
    assert store.consume_oauth_state is oauth_state_safety.consume_oauth_state_atomic
    assert connectors.consume_oauth_state is oauth_state_safety.consume_oauth_state_atomic
