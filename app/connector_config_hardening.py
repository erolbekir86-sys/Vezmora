from __future__ import annotations

import os
import sys
from typing import Any, Awaitable, Callable

from fastapi import HTTPException

from . import connectors as _connectors


ConnectorCallable = Callable[..., Any]
AsyncConnectorCallable = Callable[..., Awaitable[dict[str, object]]]


_original_connector_readiness: ConnectorCallable = _connectors.connector_readiness
_original_google_authorization_url: ConnectorCallable = _connectors.google_authorization_url
_original_meta_authorization_url: ConnectorCallable = _connectors.meta_authorization_url
_original_google_callback: AsyncConnectorCallable = _connectors.google_callback
_original_meta_callback: AsyncConnectorCallable = _connectors.meta_callback
_original_refresh_google_access_token = _connectors._refresh_google_access_token
_original_fernet = _connectors._fernet


def _configured(name: str) -> bool:
    """Treat empty and whitespace-only connector configuration as missing."""
    return bool((os.getenv(name) or "").strip())


def connector_readiness_hardened() -> dict[str, dict[str, object]]:
    result = _original_connector_readiness()
    result["google"]["configured"] = all(
        _configured(name)
        for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI")
    )
    result["meta"]["configured"] = all(
        _configured(name)
        for name in ("META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI")
    )
    return result


def google_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("GOOGLE_CLIENT_ID", "GOOGLE_REDIRECT_URI")):
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    return _original_google_authorization_url(workspace_id, user_id)


def meta_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("META_APP_ID", "META_REDIRECT_URI")):
        raise HTTPException(status_code=503, detail="Meta OAuth is not configured")
    return _original_meta_authorization_url(workspace_id, user_id)


async def google_callback_hardened(code: str, state: str) -> dict[str, object]:
    if not all(
        _configured(name)
        for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI")
    ):
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    return await _original_google_callback(code, state)


async def meta_callback_hardened(code: str, state: str) -> dict[str, object]:
    if not all(
        _configured(name)
        for name in ("META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI")
    ):
        raise HTTPException(status_code=503, detail="Meta OAuth is not configured")
    return await _original_meta_callback(code, state)


async def refresh_google_access_token_hardened(workspace_id: int, connector: dict) -> tuple[str, dict]:
    for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"):
        value = os.getenv(name)
        if value is not None and not value.strip():
            raise HTTPException(status_code=503, detail="Google OAuth configuration is incomplete")
    return await _original_refresh_google_access_token(workspace_id, connector)


def fernet_hardened():
    if not _configured("VEZMORA_SECRET_KEY"):
        raise HTTPException(status_code=503, detail="VEZMORA_SECRET_KEY is required for OAuth token storage")
    return _original_fernet()


def _install() -> None:
    _connectors.connector_readiness = connector_readiness_hardened
    _connectors.google_authorization_url = google_authorization_url_hardened
    _connectors.meta_authorization_url = meta_authorization_url_hardened
    _connectors.google_callback = google_callback_hardened
    _connectors.meta_callback = meta_callback_hardened
    _connectors._refresh_google_access_token = refresh_google_access_token_hardened
    _connectors._fernet = fernet_hardened

    # app.main imports connector callables directly. It is already loaded when
    # app.__init__ installs hardening modules, so update those bound globals too.
    app_main = sys.modules.get("app.main")
    if app_main is not None:
        app_main.connector_readiness = connector_readiness_hardened
        app_main.google_authorization_url = google_authorization_url_hardened
        app_main.meta_authorization_url = meta_authorization_url_hardened
        app_main.google_callback = google_callback_hardened
        app_main.meta_callback = meta_callback_hardened


_install()
