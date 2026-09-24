from __future__ import annotations

import base64
import hashlib
import hmac
import re
import json
import os
import secrets
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException

from .store import (
    add_notification,
    consume_oauth_state,
    get_connector,
    save_connector,
    save_oauth_state,
    update_connector_metadata,
    upsert_kpi,
    upsert_campaign_metric,
    get_workspace_settings,
    get_fx_rate,
)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/adwords",
]
META_SCOPES = ["ads_read"] + (["ads_management"] if os.getenv("VEZMORA_ENABLE_META_EXECUTION_SCOPE", "0").lower() in {"1","true","yes","on"} else [])
INSTAGRAM_SCOPES = ["pages_show_list", "pages_read_engagement", "instagram_basic", "instagram_manage_insights"]
SHOPIFY_SCOPES = ["read_orders"]
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_SCOPES = ["r_ads", "r_ads_reporting"]
_SHOPIFY_SHOP_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$", re.IGNORECASE)


def _fernet() -> Fernet:
    secret = os.getenv("VEZMORA_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=503, detail="VEZMORA_SECRET_KEY is required for OAuth token storage")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_json(value: dict) -> str:
    return _fernet().encrypt(json.dumps(value).encode("utf-8")).decode("utf-8")


def decrypt_json(value: str) -> dict:
    try:
        return json.loads(_fernet().decrypt(value.encode("utf-8")).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Stored connector token could not be decrypted") from exc


def connector_readiness() -> dict[str, dict[str, object]]:
    return {
        "google": {
            "label": "Google Analytics + Ads",
            "configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET") and os.getenv("GOOGLE_REDIRECT_URI")),
            "requirements": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"],
            "notes": "Read-only sync. Analytics needs a property ID; Google Ads needs a customer ID and API access on the OAuth client's Google Cloud project.",
        },
        "meta": {
            "label": "Meta Ads",
            "configured": bool((os.getenv("META_APP_ID") or "").strip() and (os.getenv("META_APP_SECRET") or "").strip() and (os.getenv("META_REDIRECT_URI") or "").strip()),
            "requirements": ["META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"],
            "notes": "Ads insights by default. ads_management is requested only when VEZMORA_ENABLE_META_EXECUTION_SCOPE=true.",
        },
        "instagram": {
            "label": "Instagram",
            "configured": bool((os.getenv("META_APP_ID") or "").strip() and (os.getenv("META_APP_SECRET") or "").strip() and (os.getenv("INSTAGRAM_REDIRECT_URI") or "").strip()),
            "requirements": ["META_APP_ID", "META_APP_SECRET", "INSTAGRAM_REDIRECT_URI"],
            "notes": "Read-only organic profile, media and insights for Instagram Business/Creator accounts linked through Meta.",
        },
        "shopify": {
            "label": "Shopify",
            "configured": bool((os.getenv("SHOPIFY_CLIENT_ID") or "").strip() and (os.getenv("SHOPIFY_CLIENT_SECRET") or "").strip() and (os.getenv("SHOPIFY_REDIRECT_URI") or "").strip()),
            "requirements": ["SHOPIFY_CLIENT_ID", "SHOPIFY_CLIENT_SECRET", "SHOPIFY_REDIRECT_URI"],
            "notes": "Read-only orders and products. Revenue is normalized into the workspace base currency; no store mutations are enabled.",
        },
        "linkedin": {
            "label": "LinkedIn Ads",
            "configured": bool((os.getenv("LINKEDIN_CLIENT_ID") or "").strip() and (os.getenv("LINKEDIN_CLIENT_SECRET") or "").strip() and (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip()),
            "requirements": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_REDIRECT_URI", "LinkedIn Advertising API approval"],
            "notes": "Read-only advertising analytics using r_ads and r_ads_reporting. LinkedIn must approve Advertising API access before live customer sync can work.",
        },
    }


def google_authorization_url(workspace_id: int, user_id: int) -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = secrets.token_urlsafe(28)
    save_oauth_state(state, user_id, workspace_id, "google")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def google_callback(code: str, state: str) -> dict[str, object]:
    state_row = consume_oauth_state(state, "google")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    payload = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Google token exchange failed")
    token_data = response.json()
    save_connector(
        workspace_id=state_row["workspace_id"], provider="google", status="connected", external_id=None,
        account_label="Google account", secret_blob=encrypt_json(token_data),
        metadata={"scope": token_data.get("scope"), "connected_at": datetime.now(timezone.utc).isoformat()},
    )
    return {"ok": True, "provider": "google", "workspace_id": state_row["workspace_id"]}


def meta_authorization_url(workspace_id: int, user_id: int) -> str:
    app_id = os.getenv("META_APP_ID")
    redirect_uri = os.getenv("META_REDIRECT_URI")
    if not app_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Meta OAuth is not configured")
    graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
    state = secrets.token_urlsafe(28)
    save_oauth_state(state, user_id, workspace_id, "meta")
    params = {"client_id": app_id, "redirect_uri": redirect_uri, "state": state, "scope": ",".join(META_SCOPES), "response_type": "code"}
    return f"https://www.facebook.com/{graph_version}/dialog/oauth?{urlencode(params)}"


async def meta_callback(code: str, state: str) -> dict[str, object]:
    state_row = consume_oauth_state(state, "meta")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
    params = {
        "client_id": os.getenv("META_APP_ID"), "client_secret": os.getenv("META_APP_SECRET"),
        "redirect_uri": os.getenv("META_REDIRECT_URI"), "code": code,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"https://graph.facebook.com/{graph_version}/oauth/access_token", params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Meta token exchange failed")
    token_data = response.json()
    save_connector(
        workspace_id=state_row["workspace_id"], provider="meta", status="connected", external_id=None,
        account_label="Meta account", secret_blob=encrypt_json(token_data),
        metadata={"connected_at": datetime.now(timezone.utc).isoformat(), "scope": ",".join(META_SCOPES)},
    )
    return {"ok": True, "provider": "meta", "workspace_id": state_row["workspace_id"]}


def instagram_authorization_url(workspace_id: int, user_id: int) -> str:
    app_id = (os.getenv("META_APP_ID") or "").strip()
    redirect_uri = (os.getenv("INSTAGRAM_REDIRECT_URI") or "").strip()
    if not app_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Instagram OAuth is not configured")
    graph_version = (os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
    state = secrets.token_urlsafe(28)
    save_oauth_state(state, user_id, workspace_id, "instagram")
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": ",".join(INSTAGRAM_SCOPES),
        "response_type": "code",
    }
    return f"https://www.facebook.com/{graph_version}/dialog/oauth?{urlencode(params)}"


async def instagram_callback(code: str, state: str) -> dict[str, object]:
    state_row = consume_oauth_state(state, "instagram")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    graph_version = (os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
    params = {
        "client_id": (os.getenv("META_APP_ID") or "").strip(),
        "client_secret": (os.getenv("META_APP_SECRET") or "").strip(),
        "redirect_uri": (os.getenv("INSTAGRAM_REDIRECT_URI") or "").strip(),
        "code": code,
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        response = await client.get(
            f"https://graph.facebook.com/{graph_version}/oauth/access_token",
            params=params,
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Instagram token exchange failed")
        user_token = response.json()
        user_access_token = str(user_token.get("access_token") or "").strip()
        if not user_access_token:
            raise HTTPException(status_code=502, detail="Instagram token exchange returned no access token")
        accounts = await client.get(
            f"https://graph.facebook.com/{graph_version}/me/accounts",
            params={
                "access_token": user_access_token,
                "fields": "id,name,access_token,instagram_business_account{id,username,name}",
                "limit": 100,
            },
        )
    if accounts.status_code >= 400:
        raise HTTPException(status_code=502, detail="Instagram account discovery failed")
    candidates = [
        page for page in accounts.json().get("data", [])
        if isinstance(page, dict) and isinstance(page.get("instagram_business_account"), dict)
    ]
    if not candidates:
        raise HTTPException(
            status_code=409,
            detail="No Instagram Business or Creator account linked to a managed Facebook Page was found",
        )
    page = candidates[0]
    ig = page["instagram_business_account"]
    ig_id = str(ig.get("id") or "").strip()
    page_token = str(page.get("access_token") or "").strip()
    if not ig_id or not page_token:
        raise HTTPException(status_code=502, detail="Instagram account discovery returned incomplete credentials")
    username = str(ig.get("username") or ig.get("name") or page.get("name") or "Instagram account").strip()
    token_payload = {
        "access_token": page_token,
        "user_access_token": user_access_token,
        "page_access_token": page_token,
    }
    save_connector(
        workspace_id=state_row["workspace_id"],
        provider="instagram",
        status="connected",
        external_id=ig_id,
        account_label=f"@{username}" if username and not username.startswith("@") else username,
        secret_blob=encrypt_json(token_payload),
        metadata={
            "instagram_user_id": ig_id,
            "page_id": str(page.get("id") or ""),
            "page_name": str(page.get("name") or ""),
            "username": username,
            "scope": ",".join(INSTAGRAM_SCOPES),
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        },
    )
    return {"ok": True, "provider": "instagram", "workspace_id": state_row["workspace_id"]}


def _normalize_shopify_shop(value: str) -> str:
    shop = str(value or "").strip().lower()
    if shop.startswith("https://"):
        shop = shop[8:]
    elif shop.startswith("http://"):
        shop = shop[7:]
    shop = shop.split("/", 1)[0].strip(".")
    if "." not in shop:
        if shop in {"localhost", "local"}:
            raise HTTPException(status_code=400, detail="Enter a valid *.myshopify.com store domain")
        shop = f"{shop}.myshopify.com"
    if not _SHOPIFY_SHOP_RE.fullmatch(shop):
        raise HTTPException(status_code=400, detail="Enter a valid *.myshopify.com store domain")
    return shop


def shopify_authorization_url(workspace_id: int, user_id: int, shop: str) -> str:
    client_id = (os.getenv("SHOPIFY_CLIENT_ID") or "").strip()
    redirect_uri = (os.getenv("SHOPIFY_REDIRECT_URI") or "").strip()
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Shopify OAuth is not configured")
    shop_domain = _normalize_shopify_shop(shop)
    state = secrets.token_urlsafe(28)
    save_oauth_state(state, user_id, workspace_id, "shopify")
    params = {
        "client_id": client_id,
        "scope": ",".join(SHOPIFY_SCOPES),
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"


def _verify_shopify_hmac(query: dict[str, str], supplied_hmac: str) -> bool:
    secret = (os.getenv("SHOPIFY_CLIENT_SECRET") or "").strip()
    if not secret or not supplied_hmac:
        return False
    message = urlencode(sorted((str(k), str(v)) for k, v in query.items() if k not in {"hmac", "signature"}))
    expected = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied_hmac)


async def shopify_callback(
    code: str,
    state: str,
    shop: str,
    supplied_hmac: str,
    query: dict[str, str],
) -> dict[str, object]:
    shop_domain = _normalize_shopify_shop(shop)
    if not _verify_shopify_hmac(query, supplied_hmac):
        raise HTTPException(status_code=400, detail="Invalid Shopify callback signature")
    state_row = consume_oauth_state(state, "shopify")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    payload = {
        "client_id": (os.getenv("SHOPIFY_CLIENT_ID") or "").strip(),
        "client_secret": (os.getenv("SHOPIFY_CLIENT_SECRET") or "").strip(),
        "code": code,
        "expiring": "1",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        response = await client.post(
            f"https://{shop_domain}/admin/oauth/access_token",
            data=payload,
            headers={"Accept": "application/json"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Shopify token exchange failed")
    token_data = response.json()
    access_token = str(token_data.get("access_token") or "").strip()
    if not access_token:
        raise HTTPException(status_code=502, detail="Shopify token exchange returned no access token")
    granted_scopes = {
        scope.strip() for scope in str(token_data.get("scope") or "").split(",") if scope.strip()
    }
    missing_scopes = [scope for scope in SHOPIFY_SCOPES if scope not in granted_scopes]
    if missing_scopes:
        raise HTTPException(status_code=409, detail="Shopify did not grant the required read-only order scope")
    expires_in = int(token_data.get("expires_in") or 0)
    if expires_in > 0:
        token_data["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    save_connector(
        workspace_id=state_row["workspace_id"],
        provider="shopify",
        status="connected",
        external_id=shop_domain,
        account_label=shop_domain,
        secret_blob=encrypt_json(token_data),
        metadata={
            "shop_domain": shop_domain,
            "scope": str(token_data.get("scope") or ",".join(SHOPIFY_SCOPES)),
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        },
    )
    return {"ok": True, "provider": "shopify", "workspace_id": state_row["workspace_id"]}


async def _shopify_access_token(workspace_id: int, connector: dict) -> str:
    if not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Shopify is not connected")
    token = decrypt_json(connector["secret_blob"])
    access_token = str(token.get("access_token") or "").strip()
    refresh_token = str(token.get("refresh_token") or "").strip()
    metadata = connector.get("metadata") or {}
    shop_domain = _normalize_shopify_shop(str(metadata.get("shop_domain") or connector.get("external_id") or ""))
    expires_at_raw = str(token.get("expires_at") or "").strip()
    needs_refresh = not access_token
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            needs_refresh = needs_refresh or expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5)
        except ValueError:
            needs_refresh = True
    if needs_refresh:
        if not refresh_token:
            raise HTTPException(status_code=409, detail="Shopify access expired; reconnect Shopify")
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.post(
                f"https://{shop_domain}/admin/oauth/access_token",
                data={
                    "client_id": (os.getenv("SHOPIFY_CLIENT_ID") or "").strip(),
                    "client_secret": (os.getenv("SHOPIFY_CLIENT_SECRET") or "").strip(),
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Accept": "application/json"},
            )
        if response.status_code == 401:
            raise HTTPException(status_code=409, detail="Shopify access expired; reconnect Shopify")
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Shopify token refresh failed")
        refreshed = response.json()
        refreshed_access = str(refreshed.get("access_token") or "").strip()
        if not refreshed_access:
            raise HTTPException(status_code=502, detail="Shopify token refresh returned no access token")
        expires_in = int(refreshed.get("expires_in") or 0)
        if expires_in > 0:
            refreshed["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
        save_connector(
            workspace_id,
            "shopify",
            connector.get("status", "connected"),
            connector.get("external_id"),
            connector.get("account_label"),
            encrypt_json(refreshed),
            metadata,
        )
        access_token = refreshed_access
    return access_token


def linkedin_authorization_url(workspace_id: int, user_id: int) -> str:
    client_id = (os.getenv("LINKEDIN_CLIENT_ID") or "").strip()
    redirect_uri = (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip()
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="LinkedIn OAuth is not configured")
    state = secrets.token_urlsafe(28)
    save_oauth_state(state, user_id, workspace_id, "linkedin")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": " ".join(LINKEDIN_SCOPES),
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"


async def linkedin_callback(code: str, state: str) -> dict[str, object]:
    state_row = consume_oauth_state(state, "linkedin")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip(),
        "client_id": (os.getenv("LINKEDIN_CLIENT_ID") or "").strip(),
        "client_secret": (os.getenv("LINKEDIN_CLIENT_SECRET") or "").strip(),
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data=payload,
            headers={"Accept": "application/json"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="LinkedIn token exchange failed")
    token_data = response.json()
    access_token = str(token_data.get("access_token") or "").strip()
    if not access_token:
        raise HTTPException(status_code=502, detail="LinkedIn token exchange returned no access token")
    expires_in = int(token_data.get("expires_in") or 0)
    if expires_in > 0:
        token_data["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    save_connector(
        workspace_id=state_row["workspace_id"],
        provider="linkedin",
        status="connected",
        external_id=None,
        account_label="LinkedIn Ads",
        secret_blob=encrypt_json(token_data),
        metadata={
            "scope": " ".join(LINKEDIN_SCOPES),
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        },
    )
    return {"ok": True, "provider": "linkedin", "workspace_id": state_row["workspace_id"]}


async def _linkedin_access_token(workspace_id: int, connector: dict) -> str:
    if not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="LinkedIn is not connected")
    token = decrypt_json(connector["secret_blob"])
    access_token = str(token.get("access_token") or "").strip()
    expires_at_raw = str(token.get("expires_at") or "").strip()
    needs_refresh = not access_token
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            needs_refresh = needs_refresh or expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5)
        except ValueError:
            needs_refresh = True
    if not needs_refresh:
        return access_token

    refresh_token = str(token.get("refresh_token") or "").strip()
    if not refresh_token:
        raise HTTPException(status_code=409, detail="LinkedIn access expired; reconnect LinkedIn")
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": (os.getenv("LINKEDIN_CLIENT_ID") or "").strip(),
        "client_secret": (os.getenv("LINKEDIN_CLIENT_SECRET") or "").strip(),
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data=payload,
            headers={"Accept": "application/json"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=409, detail="LinkedIn access expired; reconnect LinkedIn")
    refreshed = response.json()
    refreshed_access = str(refreshed.get("access_token") or "").strip()
    if not refreshed_access:
        raise HTTPException(status_code=502, detail="LinkedIn token refresh returned no access token")
    if not refreshed.get("refresh_token"):
        refreshed["refresh_token"] = refresh_token
    expires_in = int(refreshed.get("expires_in") or 0)
    if expires_in > 0:
        refreshed["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    save_connector(
        workspace_id,
        "linkedin",
        connector.get("status", "connected"),
        connector.get("external_id"),
        connector.get("account_label"),
        encrypt_json(refreshed),
        connector.get("metadata") or {},
    )
    return refreshed_access


def _linkedin_headers(access_token: str) -> dict[str, str]:
    api_version = (os.getenv("LINKEDIN_API_VERSION") or "202608").strip()
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Linkedin-Version": api_version,
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _linkedin_date_range(start_date: str, end_date: str) -> str:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    return (
        f"(start:(year:{start.year},month:{start.month},day:{start.day}),"
        f"end:(year:{end.year},month:{end.month},day:{end.day}))"
    )


async def sync_linkedin(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = get_connector(workspace_id, "linkedin", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect LinkedIn before syncing")
    metadata = connector.get("metadata") or {}
    account_id = re.sub(r"[^0-9]", "", str(metadata.get("ad_account_id") or ""))
    if not account_id:
        raise HTTPException(status_code=409, detail="LinkedIn Ad Account ID is missing")

    access_token = await _linkedin_access_token(workspace_id, connector)
    headers = _linkedin_headers(access_token)
    start_date, end_date = _date_range(days)
    base_currency = str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()

    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        account_response = await client.get(
            f"https://api.linkedin.com/rest/adAccounts/{account_id}",
            headers=headers,
        )
        if account_response.status_code == 403:
            raise HTTPException(status_code=409, detail="LinkedIn Advertising API access or ad-account permission is missing")
        if account_response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"LinkedIn ad-account lookup failed ({account_response.status_code})")
        account = account_response.json()

        analytics_response = await client.get(
            "https://api.linkedin.com/rest/adAnalytics",
            headers=headers,
            params={
                "q": "analytics",
                "pivot": "CAMPAIGN",
                "timeGranularity": "DAILY",
                "accounts": f"List(urn:li:sponsoredAccount:{account_id})",
                "dateRange": _linkedin_date_range(start_date, end_date),
                "fields": "impressions,clicks,externalWebsiteConversions,costInLocalCurrency,conversionValueInLocalCurrency,dateRange,pivotValues",
            },
        )
    if analytics_response.status_code == 403:
        raise HTTPException(status_code=409, detail="LinkedIn r_ads/r_ads_reporting access or ad-account permission is missing")
    if analytics_response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"LinkedIn Ads reporting sync failed ({analytics_response.status_code})")

    payload = analytics_response.json()
    rows = payload.get("elements") or []
    account_currency = str(account.get("currency") or base_currency).upper()
    rate = get_fx_rate(workspace_id, account_currency)
    warnings: list[str] = []
    if rate is None:
        warnings.append(
            f"Missing FX rate for LinkedIn Ads {account_currency} → {base_currency}; raw campaign rows were saved but aggregate KPI was skipped"
        )

    daily: dict[str, dict[str, float]] = {}
    campaign_rows = 0
    for row in rows:
        date_info = ((row.get("dateRange") or {}).get("start") or {})
        try:
            metric_date = f"{int(date_info.get('year')):04d}-{int(date_info.get('month')):02d}-{int(date_info.get('day')):02d}"
        except (TypeError, ValueError):
            continue
        pivots = row.get("pivotValues") or []
        campaign_urn = str(pivots[0] if pivots else "")
        campaign_id = campaign_urn.rsplit(":", 1)[-1] if campaign_urn else f"account-{account_id}"
        impressions = int(row.get("impressions") or 0)
        clicks = int(row.get("clicks") or 0)
        conversions = float(row.get("externalWebsiteConversions") or 0)
        spend = float(row.get("costInLocalCurrency") or 0)
        revenue = float(row.get("conversionValueInLocalCurrency") or 0)

        upsert_campaign_metric(
            workspace_id,
            {
                "provider": "linkedin_ads",
                "external_campaign_id": campaign_id,
                "campaign_name": f"LinkedIn Campaign {campaign_id}",
                "date": metric_date,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "spend": spend,
                "revenue": revenue,
                "currency": account_currency,
            },
        )
        campaign_rows += 1

        if rate is not None:
            bucket = daily.setdefault(
                metric_date,
                {"impressions": 0.0, "clicks": 0.0, "conversions": 0.0, "spend": 0.0, "revenue": 0.0},
            )
            bucket["impressions"] += impressions
            bucket["clicks"] += clicks
            bucket["conversions"] += conversions
            bucket["spend"] += spend * rate
            bucket["revenue"] += revenue * rate

    for metric_date, bucket in daily.items():
        upsert_kpi(
            workspace_id,
            {
                "date": metric_date,
                "impressions": int(bucket["impressions"]),
                "clicks": int(bucket["clicks"]),
                "leads": 0,
                "conversions": int(round(bucket["conversions"])),
                "spend_sek": bucket["spend"],
                "revenue_sek": bucket["revenue"],
                "source": "linkedin_ads",
                "currency": base_currency,
            },
        )

    result = {
        "ads_rows": len(daily),
        "campaign_rows": campaign_rows,
        "account": str(account.get("name") or account_id),
        "currency": account_currency,
        "base_currency": base_currency,
        "date_range": {"start": start_date, "end": end_date},
        "warnings": warnings,
        "read_only": True,
    }
    update_connector_metadata(
        workspace_id,
        "linkedin",
        {
            "ad_account_id": account_id,
            "account_name": result["account"],
            "account_currency": account_currency,
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "last_sync": result,
        },
    )
    add_notification(workspace_id, "sync", "LinkedIn sync complete", f"Synced {campaign_rows} daily campaign rows.", result)
    return result


async def sync_instagram(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = get_connector(workspace_id, "instagram", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect Instagram before syncing")
    metadata = connector.get("metadata") or {}
    ig_id = str(metadata.get("instagram_user_id") or connector.get("external_id") or "").strip()
    if not ig_id:
        raise HTTPException(status_code=409, detail="Instagram account ID is missing")
    token = decrypt_json(connector["secret_blob"])
    access_token = str(token.get("page_access_token") or token.get("access_token") or "").strip()
    if not access_token:
        raise HTTPException(status_code=409, detail="Instagram connector has no access token")
    graph_version = (os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
    start_date, end_date = _date_range(days)
    media_rows: list[dict[str, object]] = []
    page_url = f"https://graph.facebook.com/{graph_version}/{ig_id}/media"
    params: dict[str, object] | None = {
        "access_token": access_token,
        "fields": "media_type,media_product_type,timestamp,like_count,comments_count",
        "limit": 100,
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        profile = await client.get(
            f"https://graph.facebook.com/{graph_version}/{ig_id}",
            params={"access_token": access_token, "fields": "id,username,name,followers_count,media_count"},
        )
        if profile.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Instagram profile sync failed ({profile.status_code})")
        profile_data = profile.json()
        pages = 0
        while page_url and pages < 5:
            response = await client.get(page_url, params=params)
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Instagram media sync failed ({response.status_code})")
            payload = response.json()
            for row in payload.get("data", []):
                timestamp = str(row.get("timestamp") or "")
                media_date = timestamp[:10]
                if media_date and start_date <= media_date <= end_date:
                    media_rows.append(row)
            next_url = str((payload.get("paging") or {}).get("next") or "").strip()
            page_url = next_url or ""
            params = None
            pages += 1
    likes = sum(int(row.get("like_count") or 0) for row in media_rows)
    comments = sum(int(row.get("comments_count") or 0) for row in media_rows)
    result = {
        "media_rows": len(media_rows),
        "followers": int(profile_data.get("followers_count") or 0),
        "media_count": int(profile_data.get("media_count") or 0),
        "likes": likes,
        "comments": comments,
        "username": str(profile_data.get("username") or metadata.get("username") or ""),
        "date_range": {"start": start_date, "end": end_date},
        "warnings": [],
        "read_only": True,
    }
    update_connector_metadata(
        workspace_id,
        "instagram",
        {
            "username": result["username"],
            "followers_count": result["followers"],
            "media_count": result["media_count"],
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "last_sync": result,
        },
    )
    add_notification(workspace_id, "sync", "Instagram sync complete", f"Synced {len(media_rows)} recent media rows.", result)
    return result


async def sync_shopify(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = get_connector(workspace_id, "shopify", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect Shopify before syncing")
    metadata = connector.get("metadata") or {}
    shop_domain = _normalize_shopify_shop(str(metadata.get("shop_domain") or connector.get("external_id") or ""))
    access_token = await _shopify_access_token(workspace_id, connector)
    api_version = (os.getenv("SHOPIFY_API_VERSION") or "2026-07").strip()
    start_date, end_date = _date_range(min(days, 60))
    warnings: list[str] = []
    if days > 60:
        warnings.append("Shopify standard read_orders access is limited to the most recent 60 days; this sync was capped to 60 days")
    endpoint = f"https://{shop_domain}/admin/api/{api_version}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    shop_query = "query VexmeraShop { shop { name currencyCode } }"
    orders_query = """query VexmeraOrders($first: Int!, $after: String, $query: String!) {
      orders(first: $first, after: $after, query: $query, sortKey: CREATED_AT) {
        edges { cursor node { createdAt cancelledAt currentTotalPriceSet { shopMoney { amount currencyCode } } } }
        pageInfo { hasNextPage endCursor }
      }
    }"""
    async with httpx.AsyncClient(timeout=35, follow_redirects=False) as client:
        shop_response = await client.post(endpoint, headers=headers, json={"query": shop_query})
        if shop_response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Shopify shop lookup failed ({shop_response.status_code})")
        shop_payload = shop_response.json()
        if shop_payload.get("errors"):
            raise HTTPException(status_code=502, detail="Shopify shop lookup returned GraphQL errors")
        shop_data = (shop_payload.get("data") or {}).get("shop") or {}
        shop_currency = str(shop_data.get("currencyCode") or "SEK").upper()

        daily: dict[str, dict[str, float]] = {}
        after: str | None = None
        order_count = 0
        page_count = 0
        while page_count < 20:
            variables = {
                "first": 100,
                "after": after,
                "query": f"created_at:>={start_date} created_at:<={end_date}T23:59:59Z",
            }
            response = await client.post(endpoint, headers=headers, json={"query": orders_query, "variables": variables})
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Shopify orders sync failed ({response.status_code})")
            payload = response.json()
            if payload.get("errors"):
                raise HTTPException(status_code=502, detail="Shopify orders sync returned GraphQL errors")
            orders = ((payload.get("data") or {}).get("orders") or {})
            for edge in orders.get("edges", []):
                order = edge.get("node") or {}
                created_date = str(order.get("createdAt") or "")[:10]
                if not created_date:
                    continue
                money = (((order.get("currentTotalPriceSet") or {}).get("shopMoney")) or {})
                try:
                    amount = float(money.get("amount") or 0)
                except (TypeError, ValueError):
                    amount = 0.0
                currency = str(money.get("currencyCode") or shop_currency).upper()
                bucket = daily.setdefault(created_date, {"orders": 0.0, "revenue": 0.0})
                if not order.get("cancelledAt"):
                    bucket["orders"] += 1
                    rate = get_fx_rate(workspace_id, currency)
                    if rate is None:
                        warning = f"Missing FX rate for Shopify {currency} → {str(get_workspace_settings(workspace_id).get('base_currency') or 'SEK').upper()}; revenue KPI was skipped for affected orders"
                        if warning not in warnings:
                            warnings.append(warning)
                    else:
                        bucket["revenue"] += amount * rate
                order_count += 1
            page_info = orders.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            after = str(page_info.get("endCursor") or "").strip() or None
            if not after:
                break
            page_count += 1

    base_currency = str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()
    for metric_date, bucket in daily.items():
        upsert_kpi(
            workspace_id,
            {
                "date": metric_date,
                "impressions": 0,
                "clicks": 0,
                "leads": 0,
                "conversions": int(bucket["orders"]),
                "spend_sek": 0,
                "revenue_sek": bucket["revenue"],
                "source": "shopify_orders",
                "currency": base_currency,
            },
        )
    result = {
        "order_rows": order_count,
        "revenue_rows": len(daily),
        "shop": str(shop_data.get("name") or shop_domain),
        "currency": shop_currency,
        "base_currency": base_currency,
        "date_range": {"start": start_date, "end": end_date},
        "warnings": warnings,
        "read_only": True,
    }
    update_connector_metadata(
        workspace_id,
        "shopify",
        {
            "shop_name": result["shop"],
            "shop_currency": shop_currency,
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "last_sync": result,
        },
    )
    add_notification(workspace_id, "sync", "Shopify sync complete", f"Synced {order_count} orders.", result)
    return result


def save_connector_settings(workspace_id: int, settings: dict[str, str | None]) -> None:
    google_updates = {k: settings.get(k) for k in ("analytics_property_id", "ads_customer_id") if settings.get(k)}
    meta_updates = {"ad_account_id": settings.get("meta_ad_account_id")} if settings.get("meta_ad_account_id") else {}
    linkedin_updates = {"ad_account_id": settings.get("linkedin_ad_account_id")} if settings.get("linkedin_ad_account_id") else {}
    if google_updates:
        update_connector_metadata(workspace_id, "google", google_updates)
    if meta_updates:
        update_connector_metadata(workspace_id, "meta", meta_updates)
    if linkedin_updates:
        update_connector_metadata(workspace_id, "linkedin", linkedin_updates)


async def _refresh_google_access_token(workspace_id: int, connector: dict) -> tuple[str, dict]:
    if not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Google is not connected")
    token = decrypt_json(connector["secret_blob"])
    refresh_token = token.get("refresh_token")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if refresh_token and client_id and client_secret:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data={
                "client_id": client_id, "client_secret": client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token",
            })
        if response.status_code < 400:
            refreshed = response.json()
            token.update(refreshed)
            token["refresh_token"] = refresh_token
            save_connector(
                workspace_id, "google", connector.get("status", "connected"), connector.get("external_id"),
                connector.get("account_label"), encrypt_json(token), connector.get("metadata") or {},
            )
        elif not token.get("access_token"):
            raise HTTPException(status_code=502, detail="Google access-token refresh failed")
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=409, detail="Google connector has no access token")
    return access_token, token


def _date_range(days: int) -> tuple[str, str]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=max(days - 1, 0))
    return start.isoformat(), end.isoformat()


async def _discover_analytics_property(
    headers: dict[str, str],
) -> tuple[str | None, list[dict[str, str]], str | None]:
    """Discover GA4 properties available to the already-authorized Google user."""
    properties: dict[str, dict[str, str]] = {}
    page_token: str | None = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                params: dict[str, str] = {"pageSize": "200"}
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
                    headers=headers,
                    params=params,
                )
                if response.status_code >= 400:
                    return None, [], f"Analytics property discovery failed ({response.status_code})"
                payload = response.json()
                for account in payload.get("accountSummaries", []):
                    for property_summary in account.get("propertySummaries", []):
                        resource_name = str(property_summary.get("property") or "").strip()
                        property_id = resource_name.removeprefix("properties/")
                        if not property_id.isdigit():
                            continue
                        properties[property_id] = {
                            "id": property_id,
                            "name": str(property_summary.get("displayName") or property_id),
                        }
                page_token = str(payload.get("nextPageToken") or "").strip() or None
                if not page_token:
                    break
    except (httpx.TransportError, ValueError, TypeError):
        return None, [], "Analytics property discovery failed"

    choices = list(properties.values())
    if len(choices) == 1:
        return choices[0]["id"], choices, None
    if len(choices) > 1:
        return None, choices, "Multiple GA4 properties found; enter one Property ID"
    return None, [], "No GA4 properties found for this Google account"


async def sync_google(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = get_connector(workspace_id, "google", include_secret=True)
    if not connector or connector.get("status") != "connected":
        raise HTTPException(status_code=409, detail="Connect Google before syncing")
    metadata = connector.get("metadata") or {}
    access_token, _ = await _refresh_google_access_token(workspace_id, connector)
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    start_date, end_date = _date_range(days)
    base_currency = str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()
    synced = {"analytics_rows": 0, "ads_rows": 0, "campaign_rows": 0, "base_currency": base_currency, "warnings": []}

    property_id = (metadata.get("analytics_property_id") or "").replace("properties/", "")
    discovery_warning: str | None = None
    if not property_id:
        property_id, discovered_properties, discovery_warning = await _discover_analytics_property(headers)
        if discovered_properties:
            update_connector_metadata(
                workspace_id,
                "google",
                {"available_analytics_properties": discovered_properties},
            )
        if property_id:
            update_connector_metadata(
                workspace_id,
                "google",
                {
                    "analytics_property_id": property_id,
                    "analytics_property_name": discovered_properties[0]["name"],
                },
            )
    if property_id:
        payload = {
            "dimensions": [{"name": "date"}],
            "metrics": [{"name": "sessions"}, {"name": "keyEvents"}, {"name": "purchaseRevenue"}],
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "currencyCode": base_currency,
            "limit": "100",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport", headers=headers, json=payload)
        if response.status_code < 400:
            for row in response.json().get("rows", []):
                d = row.get("dimensionValues", [{}])[0].get("value", "")
                if len(d) == 8:
                    d = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                values = [m.get("value", "0") for m in row.get("metricValues", [])]
                upsert_kpi(workspace_id, {
                    "date": d, "impressions": 0, "clicks": int(float(values[0] or 0)), "leads": 0,
                    "conversions": int(float(values[1] or 0)), "spend_sek": 0,
                    "revenue_sek": float(values[2] or 0), "source": "google_analytics", "currency": base_currency,
                })
                synced["analytics_rows"] += 1
        else:
            synced["warnings"].append(f"Analytics sync failed ({response.status_code})")
    else:
        synced["warnings"].append(discovery_warning or "Google Analytics property ID is missing")

    customer_id = "".join(ch for ch in str(metadata.get("ads_customer_id") or "") if ch.isdigit())
    if customer_id:
        api_version = os.getenv("GOOGLE_ADS_API_VERSION", "v25")
        query = f"""SELECT segments.date, customer.currency_code, campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.conversions, metrics.conversions_value, metrics.cost_micros FROM campaign WHERE segments.date BETWEEN '{start_date}' AND '{end_date}' ORDER BY segments.date"""
        ads_headers = dict(headers)
        login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        if login_customer_id:
            ads_headers["login-customer-id"] = "".join(ch for ch in login_customer_id if ch.isdigit())
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}/googleAds:searchStream",
                headers=ads_headers, json={"query": query},
            )
        if response.status_code < 400:
            batches = response.json()
            results = [r for batch in batches for r in batch.get("results", [])]
            daily: dict[str, dict[str, float]] = {}
            for r in results:
                segments, metrics, customer = r.get("segments", {}), r.get("metrics", {}), r.get("customer", {})
                campaign = r.get("campaign", {})
                currency = (customer.get("currencyCode") or customer.get("currency_code") or base_currency).upper()
                spend = float(metrics.get("costMicros", metrics.get("cost_micros", 0)) or 0) / 1_000_000
                revenue = float(metrics.get("conversionsValue", metrics.get("conversions_value", 0)) or 0)
                conversions = float(metrics.get("conversions", 0) or 0)
                metric_date = segments.get("date")
                upsert_campaign_metric(workspace_id, {
                    "provider": "google_ads", "external_campaign_id": campaign.get("id"), "campaign_name": campaign.get("name") or str(campaign.get("id")),
                    "date": metric_date, "impressions": int(metrics.get("impressions", 0) or 0), "clicks": int(metrics.get("clicks", 0) or 0),
                    "conversions": conversions, "spend": spend, "revenue": revenue, "currency": currency,
                })
                synced["campaign_rows"] += 1
                rate = get_fx_rate(workspace_id, currency)
                if rate is None:
                    warning = f"Missing FX rate for Google Ads {currency} → {base_currency}; raw campaign rows were saved but aggregate KPI was skipped"
                    if warning not in synced["warnings"]: synced["warnings"].append(warning)
                    continue
                bucket = daily.setdefault(metric_date, {"impressions":0,"clicks":0,"conversions":0,"spend":0.0,"revenue":0.0})
                bucket["impressions"] += int(metrics.get("impressions", 0) or 0)
                bucket["clicks"] += int(metrics.get("clicks", 0) or 0)
                bucket["conversions"] += conversions
                bucket["spend"] += spend * rate
                bucket["revenue"] += revenue * rate
            for metric_date, bucket in daily.items():
                upsert_kpi(workspace_id, {
                    "date": metric_date, "impressions": int(bucket["impressions"]), "clicks": int(bucket["clicks"]), "leads": 0,
                    "conversions": int(round(bucket["conversions"])), "spend_sek": bucket["spend"], "revenue_sek": bucket["revenue"],
                    "source": "google_ads", "currency": base_currency,
                })
                synced["ads_rows"] += 1
        else:
            synced["warnings"].append(f"Google Ads sync failed ({response.status_code})")
    else:
        synced["warnings"].append("Google Ads customer ID is missing")

    update_connector_metadata(workspace_id, "google", {"last_sync_at": datetime.now(timezone.utc).isoformat(), "last_sync": synced})
    add_notification(workspace_id, "sync", "Google sync complete", f"Analytics rows: {synced['analytics_rows']}, Ads rows: {synced['ads_rows']}", synced)
    return synced


def _action_total(actions: list[dict] | None, names: set[str]) -> float:
    total = 0.0
    for action in actions or []:
        if action.get("action_type") in names:
            try:
                total += float(action.get("value", 0) or 0)
            except (TypeError, ValueError):
                pass
    return total


async def sync_meta(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = get_connector(workspace_id, "meta", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect Meta before syncing")
    metadata = connector.get("metadata") or {}
    ad_account = str(metadata.get("ad_account_id") or "").strip()
    if not ad_account:
        raise HTTPException(status_code=409, detail="Meta ad account ID is missing")
    if not ad_account.startswith("act_"):
        ad_account = f"act_{ad_account}"
    token = decrypt_json(connector["secret_blob"])
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=409, detail="Meta connector has no access token")
    graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
    base_currency = str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()
    start_date, end_date = _date_range(days)
    params = {
        "access_token": access_token,
        "fields": "date_start,campaign_id,campaign_name,impressions,clicks,spend,actions,action_values",
        "level": "campaign",
        "time_increment": 1,
        "time_range": json.dumps({"since": start_date, "until": end_date}),
        "limit": 100,
    }
    async with httpx.AsyncClient(timeout=40) as client:
        acct = await client.get(f"https://graph.facebook.com/{graph_version}/{ad_account}", params={"access_token": access_token, "fields": "currency,name"})
        if acct.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Meta ad account lookup failed ({acct.status_code})")
        account_data = acct.json()
        currency = (account_data.get("currency") or base_currency).upper()
        response = await client.get(f"https://graph.facebook.com/{graph_version}/{ad_account}/insights", params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Meta insights sync failed ({response.status_code})")
    rows = response.json().get("data", [])
    daily: dict[str, dict[str, float]] = {}
    rate = get_fx_rate(workspace_id, currency)
    for row in rows:
        leads = _action_total(row.get("actions"), {"lead", "onsite_conversion.lead_grouped"})
        conversions = _action_total(row.get("actions"), {"purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"})
        revenue = _action_total(row.get("action_values"), {"purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"})
        spend = float(row.get("spend", 0) or 0)
        metric_date = row.get("date_start")
        upsert_campaign_metric(workspace_id, {
            "provider":"meta_ads", "external_campaign_id":row.get("campaign_id"), "campaign_name":row.get("campaign_name") or str(row.get("campaign_id")),
            "date":metric_date, "impressions":int(row.get("impressions",0) or 0), "clicks":int(row.get("clicks",0) or 0),
            "conversions":conversions, "spend":spend, "revenue":revenue, "currency":currency,
        })
        if rate is not None:
            bucket=daily.setdefault(metric_date,{"impressions":0,"clicks":0,"leads":0,"conversions":0,"spend":0.0,"revenue":0.0})
            bucket["impressions"] += int(row.get("impressions",0) or 0); bucket["clicks"] += int(row.get("clicks",0) or 0)
            bucket["leads"] += leads; bucket["conversions"] += conversions; bucket["spend"] += spend*rate; bucket["revenue"] += revenue*rate
    warnings=[]
    if rate is None:
        warnings.append(f"Missing FX rate for Meta Ads {currency} → {base_currency}; raw campaign rows were saved but aggregate KPI was skipped")
    for metric_date,bucket in daily.items():
        upsert_kpi(workspace_id, {"date":metric_date,"impressions":int(bucket["impressions"]),"clicks":int(bucket["clicks"]),"leads":int(round(bucket["leads"])),"conversions":int(round(bucket["conversions"])),"spend_sek":bucket["spend"],"revenue_sek":bucket["revenue"],"source":"meta_ads","currency":base_currency})
    result = {"ads_rows": len(daily), "campaign_rows": len(rows), "account": account_data.get("name") or ad_account, "currency": currency, "base_currency": base_currency, "warnings": warnings}
    update_connector_metadata(workspace_id, "meta", {"last_sync_at": datetime.now(timezone.utc).isoformat(), "last_sync": result})
    add_notification(workspace_id, "sync", "Meta sync complete", f"Synced {len(rows)} daily insight rows.", result)
    return result


async def sync_all(workspace_id: int, days: int = 7) -> dict[str, object]:
    results: dict[str, object] = {}
    for provider, syncer in (("google", sync_google), ("meta", sync_meta), ("instagram", sync_instagram), ("shopify", sync_shopify), ("linkedin", sync_linkedin)):
        try:
            results[provider] = await syncer(workspace_id, days)
        except HTTPException as exc:
            results[provider] = {"error": str(exc.detail), "status": exc.status_code}
        except Exception as exc:
            results[provider] = {"error": type(exc).__name__}
    return results
