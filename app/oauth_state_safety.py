from __future__ import annotations

from typing import Any

from . import store as _store


def save_oauth_state_with_cleanup(state: str, user_id: int, workspace_id: int, provider: str) -> None:
    """Prune expired OAuth capabilities before saving one fresh state row."""
    with _store._connect() as con:
        con.execute(
            "DELETE FROM oauth_states WHERE created_at < datetime('now','-20 minutes')"
        )
        con.execute(
            "INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)",
            (state, user_id, workspace_id, provider),
        )


def consume_oauth_state_atomic(state: str, provider: str) -> dict[str, Any] | None:
    """Consume one fresh provider-scoped OAuth state in a single database claim.

    DELETE ... RETURNING makes the state a true one-time capability on both
    SQLite and PostgreSQL. A concurrent callback that loses the claim receives
    no row instead of reusing a state that another request already accepted.
    """
    with _store._connect() as con:
        row = con.execute(
            """DELETE FROM oauth_states
               WHERE state=? AND provider=?
                 AND created_at >= datetime('now','-20 minutes')
               RETURNING *""",
            (state, provider),
        ).fetchone()
    return dict(row) if row else None


def install_oauth_state_safety() -> None:
    """Install bounded, atomic OAuth-state handling before connector modules bind it."""
    if getattr(_store, "_vexmera_oauth_state_safety_installed", False):
        return
    _store.save_oauth_state = save_oauth_state_with_cleanup
    _store.consume_oauth_state = consume_oauth_state_atomic
    _store._vexmera_oauth_state_safety_installed = True
