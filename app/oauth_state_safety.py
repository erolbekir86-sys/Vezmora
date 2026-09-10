from __future__ import annotations

import hashlib
from typing import Any

from . import store as _store


def _state_hash(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def save_oauth_state_with_cleanup(state: str, user_id: int, workspace_id: int, provider: str) -> None:
    """Prune expired OAuth capabilities and persist only a hash of new state values."""
    with _store._connect() as con:
        con.execute(
            "DELETE FROM oauth_states WHERE created_at < datetime('now','-20 minutes')"
        )
        con.execute(
            "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
            (_state_hash(state), user_id, workspace_id, provider),
        )


def consume_oauth_state_atomic(state: str, provider: str) -> dict[str, Any] | None:
    """Consume one fresh provider-scoped OAuth state in a single database claim.

    New states are stored as SHA-256 hashes so the live bearer-style capability
    is not retained in the database. During the short rollout window, raw state
    matching remains accepted for states issued by the previous release. DELETE
    ... RETURNING keeps either representation single-use on SQLite/PostgreSQL.
    """
    hashed_state = _state_hash(state)
    with _store._connect() as con:
        row = con.execute(
            """DELETE FROM oauth_states
               WHERE (state=? OR state=?) AND provider=?
                 AND created_at >= datetime('now','-20 minutes')
               RETURNING *""",
            (hashed_state, state, provider),
        ).fetchone()
    return dict(row) if row else None


def install_oauth_state_safety() -> None:
    """Install bounded, atomic OAuth-state handling before connector modules bind it."""
    if getattr(_store, "_vexmera_oauth_state_safety_installed", False):
        return
    _store.save_oauth_state = save_oauth_state_with_cleanup
    _store.consume_oauth_state = consume_oauth_state_atomic
    _store._vexmera_oauth_state_safety_installed = True
