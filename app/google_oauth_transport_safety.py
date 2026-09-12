from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from . import connectors as _connectors


async def google_callback_safe(code: str, state: str) -> dict[str, object]:
    """Exchange a Google OAuth code on a fixed, non-redirecting token endpoint."""
    state_row = _connectors.consume_oauth_state(state, "google")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    payload = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.post(_connectors.GOOGLE_TOKEN_URL, data=payload)
    except httpx.TransportError:
        raise HTTPException(status_code=502, detail="Google token exchange failed") from None

    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except Exception:
            error_payload = None
        error = error_payload.get("error") if isinstance(error_payload, dict) else None
        # Only fixed messages leave the server, never Google's raw body/code.
        if error == "invalid_client":
            raise HTTPException(status_code=503, detail="Google OAuth client configuration is invalid. Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Vercel against the same Google Cloud OAuth client.")
        if error == "invalid_grant":
            raise HTTPException(status_code=409, detail="Google authorization expired or was already used. Reconnect Google; verify GOOGLE_REDIRECT_URI if this repeats.")
        raise HTTPException(status_code=502, detail="Google token exchange failed")

    try:
        token_data: Any = response.json()
    except Exception:
        token_data = None
    if not isinstance(token_data, dict) or not token_data.get("access_token"):
        raise HTTPException(status_code=502, detail="Google token exchange returned an invalid response")

    if not token_data.get("refresh_token"):
        raise HTTPException(status_code=409, detail="Google did not grant offline access. Reconnect Google and approve access so automatic sync can continue.")

    current = _connectors.get_connector(state_row["workspace_id"], "google") or {}
    previous_metadata = current.get("metadata") or {}
    # Reconnecting replaces credentials, but must not erase configured data
    # sources. Do not retain an old account's refresh token or success status.
    source_settings = {
        key: previous_metadata[key]
        for key in ("analytics_property_id", "ads_customer_id")
        if previous_metadata.get(key)
    }

    _connectors.save_connector(
        workspace_id=state_row["workspace_id"],
        provider="google",
        status="connected",
        external_id=None,
        account_label="Google account",
        secret_blob=_connectors.encrypt_json(token_data),
        metadata={
            **source_settings,
            "scope": token_data.get("scope"),
            "connected_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {"ok": True, "provider": "google", "workspace_id": state_row["workspace_id"]}


def install_google_oauth_transport_safety() -> None:
    """Install before app.main imports google_callback from connectors."""
    if getattr(_connectors, "_vexmera_google_oauth_transport_safety_installed", False):
        return
    _connectors.google_callback = google_callback_safe
    _connectors._vexmera_google_oauth_transport_safety_installed = True
