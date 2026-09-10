from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import wraps

from . import store as _store

DEFAULT_TRIAL_DAYS = 14
CURRENT_DEFAULT_PLAN = "start"

_ORIGINAL_CREATE_USER = _store.create_user
_ORIGINAL_CREATE_WORKSPACE = _store.create_workspace


def _initialize_workspace_billing(workspace_id: int) -> None:
    trial_ends_at = (datetime.now(timezone.utc) + timedelta(days=DEFAULT_TRIAL_DAYS)).isoformat()
    _store.set_workspace_billing(
        workspace_id,
        plan=CURRENT_DEFAULT_PLAN,
        billing_status="trialing",
        trial_ends_at=trial_ends_at,
    )


@wraps(_ORIGINAL_CREATE_USER)
def create_user_with_current_workspace_defaults(
    email: str,
    password_salt: str,
    password_hash: str,
    workspace_name: str,
) -> tuple[int, int]:
    user_id, workspace_id = _ORIGINAL_CREATE_USER(email, password_salt, password_hash, workspace_name)
    _initialize_workspace_billing(workspace_id)
    return user_id, workspace_id


@wraps(_ORIGINAL_CREATE_WORKSPACE)
def create_workspace_with_current_defaults(user_id: int, name: str) -> int:
    workspace_id = _ORIGINAL_CREATE_WORKSPACE(user_id, name)
    _initialize_workspace_billing(workspace_id)
    return workspace_id


def install_workspace_billing_defaults() -> None:
    """Use the current Start plan and a bounded 14-day trial for new workspaces only.

    Historical workspace rows are deliberately left untouched. Billing's existing
    plan normalizer continues to read legacy `starter` / `scale` values safely.
    """
    if getattr(_store, "_vexmera_workspace_billing_defaults_installed", False):
        return

    _store.create_user = create_user_with_current_workspace_defaults
    _store.create_workspace = create_workspace_with_current_defaults
    _store._vexmera_workspace_billing_defaults_installed = True
