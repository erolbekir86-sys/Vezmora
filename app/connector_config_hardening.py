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
_original_instagram_authorization_url: ConnectorCallable = _connectors.instagram_authorization_url
_original_shopify_authorization_url: ConnectorCallable = _connectors.shopify_authorization_url
_original_linkedin_authorization_url: ConnectorCallable = _connectors.linkedin_authorization_url
_original_fernet = _connectors._fernet


def _configured(name: str) -> bool:
    """Treat empty and whitespace-only connector configuration as missing."""
    return bool((os.getenv(name) or "").strip())


def _expected_redirect(path: str) -> str | None:
    app_url = (os.getenv("VEZMORA_APP_URL") or "").strip().rstrip("/")
    if not app_url:
        return None
    return f"{app_url}{path}"


def _redirect_ready(name: str, path: str) -> bool:
    value = (os.getenv(name) or "").strip()
    if not value:
        return False
    production_like = (os.getenv("VERCEL_ENV") or "").strip().lower() == "production"
    if not production_like:
        return value.startswith("https://") or value.startswith("http://localhost")
    expected = _expected_redirect(path)
    return bool(expected and value == expected and value.startswith("https://"))


def connector_readiness_hardened() -> dict[str, dict[str, object]]:
    result = _original_connector_readiness()
    definitions = {
        "google": (("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"), "GOOGLE_REDIRECT_URI", "/api/connectors/google/callback"),
        "meta": (("META_APP_ID", "META_APP_SECRET"), "META_REDIRECT_URI", "/api/connectors/meta/callback"),
        "instagram": (("META_APP_ID", "META_APP_SECRET"), "INSTAGRAM_REDIRECT_URI", "/api/connectors/instagram/callback"),
        "shopify": (("SHOPIFY_CLIENT_ID", "SHOPIFY_CLIENT_SECRET"), "SHOPIFY_REDIRECT_URI", "/api/connectors/shopify/callback"),
        "linkedin": (("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"), "LINKEDIN_REDIRECT_URI", "/api/connectors/linkedin/callback"),
    }
    for provider, (credential_names, redirect_name, redirect_path) in definitions.items():
        credentials_ok = all(_configured(name) for name in credential_names)
        redirect_ok = _redirect_ready(redirect_name, redirect_path)
        result[provider]["configured"] = credentials_ok and redirect_ok
        result[provider]["credentials_configured"] = credentials_ok
        result[provider]["redirect_ok"] = redirect_ok
        result[provider]["read_only"] = True
        if provider == "instagram":
            result[provider]["external_approval_required"] = True
            result[provider]["external_approval_confirmed"] = (os.getenv("INSTAGRAM_APP_REVIEW_APPROVED") or "").strip().lower() in {"1", "true", "yes", "on"}
        elif provider == "linkedin":
            result[provider]["external_approval_required"] = True
            result[provider]["external_approval_confirmed"] = (os.getenv("LINKEDIN_ADS_API_APPROVED") or "").strip().lower() in {"1", "true", "yes", "on"}
        else:
            result[provider]["external_approval_required"] = False
            result[provider]["external_approval_confirmed"] = True
    return result


def google_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("GOOGLE_CLIENT_ID", "GOOGLE_REDIRECT_URI")):
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    return _original_google_authorization_url(workspace_id, user_id)


def meta_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("META_APP_ID", "META_REDIRECT_URI")):
        raise HTTPException(status_code=503, detail="Meta OAuth is not configured")
    return _original_meta_authorization_url(workspace_id, user_id)


def instagram_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("META_APP_ID", "META_APP_SECRET")) or not _redirect_ready(
        "INSTAGRAM_REDIRECT_URI", "/api/connectors/instagram/callback"
    ):
        raise HTTPException(status_code=503, detail="Instagram OAuth is not configured for this environment")
    return _original_instagram_authorization_url(workspace_id, user_id)


def shopify_authorization_url_hardened(workspace_id: int, user_id: int, shop: str) -> str:
    if not all(_configured(name) for name in ("SHOPIFY_CLIENT_ID", "SHOPIFY_CLIENT_SECRET")) or not _redirect_ready(
        "SHOPIFY_REDIRECT_URI", "/api/connectors/shopify/callback"
    ):
        raise HTTPException(status_code=503, detail="Shopify OAuth is not configured for this environment")
    return _original_shopify_authorization_url(workspace_id, user_id, shop)


def linkedin_authorization_url_hardened(workspace_id: int, user_id: int) -> str:
    if not all(_configured(name) for name in ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET")) or not _redirect_ready(
        "LINKEDIN_REDIRECT_URI", "/api/connectors/linkedin/callback"
    ):
        raise HTTPException(status_code=503, detail="LinkedIn OAuth is not configured for this environment")
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
    _connectors.instagram_authorization_url = instagram_authorization_url_hardened
    _connectors.shopify_authorization_url = shopify_authorization_url_hardened
    _connectors.linkedin_authorization_url = linkedin_authorization_url_hardened
    _connectors._fernet = fernet_hardened

    # app.main imports these start/readiness callables directly. Patch those
    # bindings too while leaving callback wrappers untouched.
    app_main = sys.modules.get("app.main")
    if app_main is not None:
        app_main.connector_readiness = connector_readiness_hardened
        app_main.google_authorization_url = google_authorization_url_hardened
        app_main.meta_authorization_url = meta_authorization_url_hardened
        app_main.instagram_authorization_url = instagram_authorization_url_hardened
        app_main.shopify_authorization_url = shopify_authorization_url_hardened
        app_main.linkedin_authorization_url = linkedin_authorization_url_hardened


_install()
