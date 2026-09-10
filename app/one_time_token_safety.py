from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import store as _store


def consume_workspace_invite_atomic(token_hash: str, email: str) -> dict[str, Any] | None:
    """Consume an invite only when this transaction wins the one-time update."""
    now = datetime.now(timezone.utc).isoformat()
    with _store._connect() as con:
        row = con.execute(
            "SELECT * FROM workspace_invites "
            "WHERE token_hash=? AND email=? COLLATE NOCASE AND accepted_at IS NULL AND expires_at>?",
            (token_hash, email.strip(), now),
        ).fetchone()
        if not row:
            return None

        claimed = con.execute(
            "UPDATE workspace_invites SET accepted_at=CURRENT_TIMESTAMP "
            "WHERE id=? AND accepted_at IS NULL AND expires_at>?",
            (row["id"], now),
        )
        if claimed.rowcount != 1:
            return None
        return dict(row)


def consume_password_reset_atomic(token_hash: str) -> int | None:
    """Consume a password-reset token only when this transaction wins the claim."""
    now = datetime.now(timezone.utc).isoformat()
    with _store._connect() as con:
        row = con.execute(
            "SELECT * FROM password_reset_tokens "
            "WHERE token_hash=? AND used_at IS NULL AND expires_at>?",
            (token_hash, now),
        ).fetchone()
        if not row:
            return None

        claimed = con.execute(
            "UPDATE password_reset_tokens SET used_at=CURRENT_TIMESTAMP "
            "WHERE id=? AND used_at IS NULL AND expires_at>?",
            (row["id"], now),
        )
        if claimed.rowcount != 1:
            return None
        return int(row["user_id"])


def install_one_time_token_safety() -> None:
    """Install atomic one-time token claims before app.main binds store helpers."""
    if getattr(_store, "_vexmera_one_time_token_safety_installed", False):
        return

    _store.consume_workspace_invite = consume_workspace_invite_atomic
    _store.consume_password_reset = consume_password_reset_atomic
    _store._vexmera_one_time_token_safety_installed = True
