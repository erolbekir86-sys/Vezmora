from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException

from . import connectors as _connectors
from . import store as _store
from .auth import require_user

# This module is imported by app.__init__ after the existing connector patches.
# Importing app.main here finishes normal app construction first, then registers
# the privacy-control route on the same FastAPI instance.
from .main import app as _app  # noqa: E402

User = Annotated[dict[str, Any], Depends(require_user)]
_ALLOWED_PROVIDERS = {"google", "meta"}


def _require_owner_or_admin(user: dict[str, Any], workspace_id: int) -> None:
    if not _store.user_has_workspace(int(user["id"]), workspace_id):
        raise HTTPException(status_code=403, detail="Workspace access denied")
    role = _store.get_workspace_role(int(user["id"]), workspace_id)
    if role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Connector disconnect requires owner or admin role")


def _clear_local_connector(workspace_id: int, provider: str) -> bool:
    disconnected_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "disconnected_at": disconnected_at,
        "historical_data_retained": True,
    }
    with _store._connect() as con:
        row = con.execute(
            "SELECT id FROM connectors WHERE workspace_id=? AND provider=?",
            (workspace_id, provider),
        ).fetchone()
        if not row:
            return False
        con.execute(
            """UPDATE connectors
               SET status='disconnected', external_id=NULL, account_label=NULL,
                   secret_blob=NULL, metadata_json=?, updated_at=CURRENT_TIMESTAMP
               WHERE workspace_id=? AND provider=?""",
            (json.dumps(metadata), workspace_id, provider),
        )
        con.execute(
            "DELETE FROM oauth_states WHERE workspace_id=? AND provider=?",
            (workspace_id, provider),
        )
    return True


async def _revoke_provider_token(provider: str, secret_blob: str | None) -> tuple[bool, bool]:
    """Best-effort upstream revocation. Local credential deletion never depends on it."""
    if not secret_blob:
        return False, False
    try:
        token_data = _connectors.decrypt_json(secret_blob)
    except Exception:
        return False, False

    access_token = str(token_data.get("access_token") or "").strip()
    refresh_token = str(token_data.get("refresh_token") or "").strip()
    token = refresh_token or access_token
    if not token:
        return False, False

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            if provider == "google":
                response = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    data={"token": token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            else:
                graph_version = (_connectors.os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
                response = await client.delete(
                    f"https://graph.facebook.com/{graph_version}/me/permissions",
                    params={"access_token": access_token},
                )
        return True, response.status_code < 400
    except Exception:
        return True, False


@_app.post("/api/connectors/{provider}/disconnect")
async def disconnect_connector(provider: str, workspace_id: int, user: User) -> dict[str, object]:
    provider = provider.strip().lower()
    if provider not in _ALLOWED_PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown connector")
    _require_owner_or_admin(user, workspace_id)

    connector = _store.get_connector(workspace_id, provider, include_secret=True)
    attempted = False
    revoked = False
    if connector:
        attempted, revoked = await _revoke_provider_token(provider, connector.get("secret_blob"))

    existed = _clear_local_connector(workspace_id, provider)
    if existed:
        _store.add_notification(
            workspace_id,
            "connector",
            f"{provider.title()} disconnected",
            "Stored connector credentials were removed. Previously synced performance history remains in this workspace until a separate deletion flow is used.",
            {"provider": provider, "historical_data_retained": True},
        )

    return {
        "ok": True,
        "provider": provider,
        "connection_existed": existed,
        "credentials_removed": True,
        "provider_revoke_attempted": attempted,
        "provider_revoke_succeeded": revoked if attempted else None,
        "historical_data_retained": True,
    }
