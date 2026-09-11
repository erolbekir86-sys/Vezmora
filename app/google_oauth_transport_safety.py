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
        raise HTTPException(status_code=502, detail="Google token exchange failed")

    try:
        token_data: Any = response.json()
    except Exception:
        token_data = None
    if not isinstance(token_data, dict) or not token_data.get("access_token"):
        raise HTTPException(status_code=502, detail="Google token exchange returned an invalid response")

    _connectors.save_connector(
        workspace_id=state_row["workspace_id"],
        provider="google",
        status="connected",
        external_id=None,
        account_label="Google account",
        secret_blob=_connectors.encrypt_json(token_data),
        metadata={
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
