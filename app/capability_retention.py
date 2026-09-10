from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps

from . import store as _store

_ORIGINAL_CREATE_SESSION = _store.create_session
_ORIGINAL_CREATE_PASSWORD_RESET = _store.create_password_reset
_ORIGINAL_CREATE_WORKSPACE_INVITE = _store.create_workspace_invite


def _prune_expired(table: str) -> None:
    """Delete only expired rows from one fixed capability table."""
    if table not in {"sessions", "password_reset_tokens", "workspace_invites"}:
        raise ValueError("Unsupported capability table")
    now = datetime.now(timezone.utc).isoformat()
    with _store._connect() as con:
        con.execute(f"DELETE FROM {table} WHERE expires_at<=?", (now,))


@wraps(_ORIGINAL_CREATE_SESSION)
def create_session_with_retention(user_id: int, token_hash: str, expires_at: str) -> None:
    _prune_expired("sessions")
    _ORIGINAL_CREATE_SESSION(user_id, token_hash, expires_at)


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
    return _ORIGINAL_CREATE_WORKSPACE_INVITE(
        workspace_id,
        email,
        role,
        token_hash,
        invited_by,
        expires_at,
    )


def install_capability_retention() -> None:
    """Prune expired capability rows before auth/main bind creation helpers."""
    if getattr(_store, "_vexmera_capability_retention_installed", False):
        return
    _store.create_session = create_session_with_retention
    _store.create_password_reset = create_password_reset_with_retention
    _store.create_workspace_invite = create_workspace_invite_with_retention
    _store._vexmera_capability_retention_installed = True
