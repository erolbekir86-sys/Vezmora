from __future__ import annotations

import os
import sys
from typing import Any, Callable

from fastapi import HTTPException

from . import connectors as _connectors


ConnectorCallable = Callable[..., Any]


_original_connector_readiness: ConnectorCallable = _connectors.connector_readiness
_original_google_authorization_url: ConnectorCallable = _connectors.google_authorization_url
_original_meta_authorization_url: ConnectorCallable = _connectors.meta_authorization_url
_original_linkedin_authorization_url: ConnectorCallable = _connectors.linkedin_authorization_url
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
    result["linkedin"]["configured"] = all(
        _configured(name)
        for name in ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_REDIRECT_URI")
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


def linkedin_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("LINKEDIN_CLIENT_ID", "LINKEDIN_REDIRECT_URI")):
        raise HTTPException(status_code=503, detail="LinkedIn OAuth is not configured")
    return _original_linkedin_authorization_url(workspace_id, user_id)


def fernet_hardened():
    if not _configured("VEZMORA_SECRET_KEY"):
        raise HTTPException(status_code=503, detail="VEZMORA_SECRET_KEY is required for OAuth token storage")
    return _original_fernet()


def _install() -> None:
    # Keep existing callback transport-safety and token-refresh reliability
    # wrappers intact. This module only hardens configuration detection and
    # OAuth-start/token-storage boundaries where whitespace could otherwise be
    # misclassified as valid configuration.
    _connectors.connector_readiness = connector_readiness_hardened
    _connectors.google_authorization_url = google_authorization_url_hardened
    _connectors.meta_authorization_url = meta_authorization_url_hardened
    _connectors.linkedin_authorization_url = linkedin_authorization_url_hardened
    _connectors._fernet = fernet_hardened

    # app.main imports these start/readiness callables directly. Patch those
    # bindings too while leaving callback wrappers untouched.
    app_main = sys.modules.get("app.main")
    if app_main is not None:
        app_main.connector_readiness = connector_readiness_hardened
        app_main.google_authorization_url = google_authorization_url_hardened
        app_main.meta_authorization_url = meta_authorization_url_hardened
        app_main.linkedin_authorization_url = linkedin_authorization_url_hardened


_install()
