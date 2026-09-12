from __future__ import annotations

from . import store as _store


def update_user_password_and_revoke_sessions(user_id: int, password_salt: str, password_hash: str) -> None:
    """Rotate credentials and invalidate every existing authenticated session atomically."""
    with _store._connect() as con:
        con.execute(
            "UPDATE users SET password_salt=?, password_hash=? WHERE id=?",
            (password_salt, password_hash, user_id),
        )
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


def install_password_reset_session_safety() -> None:
    """Install before app.main binds update_user_password for reset confirmation."""
    if getattr(_store, "_vexmera_password_reset_session_safety_installed", False):
        return
    _store.update_user_password = update_user_password_and_revoke_sessions
    _store._vexmera_password_reset_session_safety_installed = True
