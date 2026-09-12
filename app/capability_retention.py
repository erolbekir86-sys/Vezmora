from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps

from . import store as _store

_ORIGINAL_CREATE_SESSION = _store.create_session
_ORIGINAL_CREATE_PASSWORD_RESET = _store.create_password_reset
_ORIGINAL_CREATE_WORKSPACE_INVITE = _store.create_workspace_invite
MAX_ACTIVE_SESSIONS_PER_USER = 20


def _prune_expired(table: str) -> None:
    """Delete only expired rows from one fixed capability table."""
    if table not in {"sessions", "password_reset_tokens", "workspace_invites"}:
        raise ValueError("Unsupported capability table")
    now = datetime.now(timezone.utc).isoformat()
    with _store._connect() as con:
        con.execute(f"DELETE FROM {table} WHERE expires_at<=?", (now,))


def _trim_user_sessions(user_id: int) -> None:
    """Keep only the newest bounded set of active sessions for one account."""
    with _store._connect() as con:
        con.execute(
            """DELETE FROM sessions
               WHERE user_id=?
                 AND id NOT IN (
                     SELECT id FROM sessions
                     WHERE user_id=?
                     ORDER BY created_at DESC, id DESC
                     LIMIT ?
                 )""",
            (user_id, user_id, MAX_ACTIVE_SESSIONS_PER_USER),
        )


@wraps(_ORIGINAL_CREATE_SESSION)
def create_session_with_retention(user_id: int, token_hash: str, expires_at: str) -> None:
    _prune_expired("sessions")
    _ORIGINAL_CREATE_SESSION(user_id, token_hash, expires_at)
    # A successful login may create a new device/browser session. Bound active
    # capability growth without forcing normal users into single-session auth.
    # The newest session is always kept; only the oldest excess rows are removed.
    _trim_user_sessions(user_id)


@wraps(_ORIGINAL_CREATE_PASSWORD_RESET)
def create_password_reset_with_retention(user_id: int, token_hash: str, expires_at: str) -> int:
    _prune_expired("password_reset_tokens")
    # A newly requested reset link supersedes every older reset capability for
    # the same account. This bounds the number of simultaneously valid links
    # without changing the public reset flow or token lifetime.
    with _store._connect() as con:
        con.execute("DELETE FROM password_reset_tokens WHERE user_id=?", (user_id,))
    return _ORIGINAL_CREATE_PASSWORD_RESET(user_id, token_hash, expires_at)


@wraps(_ORIGINAL_CREATE_WORKSPACE_INVITE)
def create_workspace_invite_with_retention(
    workspace_id: int,
    email: str,
    role: str,
    token_hash: str,
    invited_by: int,
    expires_at: str,
) -> int:
    _prune_expired("workspace_invites")
    # Re-inviting the same address to the same workspace supersedes any older
    # outstanding capability for that membership. Accepted invites remain as
    # audit history, and invites for other workspaces/addresses are untouched.
    with _store._connect() as con:
        con.execute(
            "DELETE FROM workspace_invites WHERE workspace_id=? AND email=? COLLATE NOCASE AND accepted_at IS NULL",
            (workspace_id, email),
        )
    return _ORIGINAL_CREATE_WORKSPACE_INVITE(
        workspace_id,
        email,
        role,
        token_hash,
        invited_by,
        expires_at,
    )


def install_capability_retention() -> None:
    """Prune and bound capability rows before auth/main bind creation helpers."""
    if getattr(_store, "_vexmera_capability_retention_installed", False):
        return
    _store.create_session = create_session_with_retention
    _store.create_password_reset = create_password_reset_with_retention
    _store.create_workspace_invite = create_workspace_invite_with_retention
    _store._vexmera_capability_retention_installed = True