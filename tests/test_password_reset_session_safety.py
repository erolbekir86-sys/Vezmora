from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app import store
from app import main as app_main
from app.auth import hash_password
from app.password_reset_session_safety import update_user_password_and_revoke_sessions


def test_password_update_is_bound_to_session_revoking_guard() -> None:
    assert store.update_user_password is update_user_password_and_revoke_sessions
    assert app_main.update_user_password is update_user_password_and_revoke_sessions


def test_password_rotation_revokes_every_existing_session_atomically(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "password-reset-sessions.db")
    store.init_db()

    old_salt, old_hash = hash_password("old-password-123")
    user_id, _ = store.create_user("session-reset@example.com", old_salt, old_hash, "Reset Session Test")
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    store.create_session(user_id, "session-one", expires_at)
    store.create_session(user_id, "session-two", expires_at)

    new_salt, new_hash = hash_password("new-password-456")
    store.update_user_password(user_id, new_salt, new_hash)

    with store._connect() as con:
        user = con.execute(
            "SELECT password_salt,password_hash FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        session_count = con.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id=?",
            (user_id,),
        ).fetchone()[0]

    assert user["password_salt"] == new_salt
    assert user["password_hash"] == new_hash
    assert session_count == 0
