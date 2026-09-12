from __future__ import annotations

from datetime import datetime, timedelta, timezone

import app.store as store
from app import capability_retention


def _future(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _prepare(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "session-cap.db")
    store.init_db()
    return store.create_user("sessions@example.com", "salt", "hash", "Sessions")[0]


def test_session_creation_keeps_only_newest_bounded_set(tmp_path, monkeypatch):
    user_id = _prepare(tmp_path, monkeypatch)
    total = capability_retention.MAX_ACTIVE_SESSIONS_PER_USER + 7

    for index in range(total):
        capability_retention.create_session_with_retention(
            user_id,
            f"session-{index:03d}",
            _future(2),
        )

    with store._connect() as con:
        rows = con.execute(
            "SELECT token_hash FROM sessions WHERE user_id=? ORDER BY id",
            (user_id,),
        ).fetchall()

    hashes = [row["token_hash"] for row in rows]
    assert len(hashes) == capability_retention.MAX_ACTIVE_SESSIONS_PER_USER
    assert "session-000" not in hashes
    assert f"session-{total - 1:03d}" in hashes


def test_session_cap_is_scoped_to_one_user(tmp_path, monkeypatch):
    first_user = _prepare(tmp_path, monkeypatch)
    second_user, _ = store.create_user("other-sessions@example.com", "salt", "hash", "Other")
    capability_retention.create_session_with_retention(second_user, "other-user-session", _future(2))

    for index in range(capability_retention.MAX_ACTIVE_SESSIONS_PER_USER + 3):
        capability_retention.create_session_with_retention(
            first_user,
            f"first-{index:03d}",
            _future(2),
        )

    with store._connect() as con:
        first_count = con.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id=?",
            (first_user,),
        ).fetchone()[0]
        second_hashes = [
            row["token_hash"]
            for row in con.execute(
                "SELECT token_hash FROM sessions WHERE user_id=?",
                (second_user,),
            ).fetchall()
        ]

    assert first_count == capability_retention.MAX_ACTIVE_SESSIONS_PER_USER
    assert second_hashes == ["other-user-session"]


def test_expired_sessions_are_pruned_before_active_cap(tmp_path, monkeypatch):
    user_id = _prepare(tmp_path, monkeypatch)
    expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with store._connect() as con:
        con.execute(
            "INSERT INTO sessions(user_id,token_hash,expires_at) VALUES(?,?,?)",
            (user_id, "expired", expired),
        )

    capability_retention.create_session_with_retention(user_id, "fresh", _future(1))

    with store._connect() as con:
        hashes = [row["token_hash"] for row in con.execute("SELECT token_hash FROM sessions").fetchall()]
    assert hashes == ["fresh"]
