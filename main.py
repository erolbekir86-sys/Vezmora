from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import HTTPException

# Vercel's deployed source bundle is read-only. Prefer persistent Postgres
# whenever DATABASE_URL/POSTGRES_URL is configured. Some early beta Vercel
# setups created empty legacy variables, so do not let empty values block the
# production bootstrap.
postgres_url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
if postgres_url:
    # Reuse the existing remote-store interface while translating Vexmera's
    # SQLite-style DB-API calls to PostgreSQL through postgres_compat.
    from app import postgres_compat as _postgres_compat

    sys.modules["turso_serverless"] = _postgres_compat
    # Override an empty/legacy TURSO_DATABASE_URL so store.py definitely uses
    # the Postgres compatibility connection when DATABASE_URL is present.
    os.environ["TURSO_DATABASE_URL"] = postgres_url

if os.getenv("VERCEL"):
    # Vercel is always serverless for this deployment. Override any empty or
    # stale beta value rather than relying on setdefault().
    os.environ["VEZMORA_SERVERLESS"] = "true"

    # Only use /tmp as a smoke-test fallback when no persistent remote database
    # is configured at all.
    if not postgres_url and not (os.getenv("TURSO_DATABASE_URL") or "").strip():
        os.environ["VEZMORA_DB_PATH"] = "/tmp/.vezmora.db"
        os.environ["VEZMORA_DATA_DIR"] = "/tmp"

# Empty environment variables should not erase safe production defaults.
if not (os.getenv("OPENAI_MODEL") or "").strip():
    os.environ["OPENAI_MODEL"] = "gpt-5.6-terra"
if not (os.getenv("META_GRAPH_VERSION") or "").strip():
    os.environ["META_GRAPH_VERSION"] = "v24.0"

# The Postgres schema is provisioned separately in Neon. Avoid running the
# SQLite bootstrap DDL against Postgres and verify connectivity instead.
if postgres_url:
    import app.store as _store

    def _verify_database() -> None:
        with _store._connect() as con:
            con.execute("SELECT 1")

    _store.init_db = _verify_database

from app.main import app, main
import app.main as _app_main
import app.connectors as _connectors

# Facebook Login for Business uses permissions from the saved Login
# Configuration. Remove the legacy scope parameter and force code response.
_original_meta_authorization_url = _app_main.meta_authorization_url


def _meta_business_authorization_url(workspace_id: int, user_id: int) -> str:
    url = _original_meta_authorization_url(workspace_id, user_id)
    config_id = (os.getenv("META_LOGIN_CONFIG_ID") or "903910732442057").strip()
    if not config_id:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.pop("scope", None)
    query["config_id"] = config_id
    query["response_type"] = "code"
    query["override_default_response_type"] = "true"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def _meta_business_callback(code: str, state: str) -> dict[str, object]:
    state_row = _connectors.consume_oauth_state(state, "meta")
    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    graph_version = (os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
    params = {
        "client_id": os.getenv("META_APP_ID"),
        "client_secret": os.getenv("META_APP_SECRET"),
        "redirect_uri": os.getenv("META_REDIRECT_URI"),
        "code": code,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"https://graph.facebook.com/{graph_version}/oauth/access_token", params=params)
    if response.status_code >= 400:
        try:
            error = (response.json() or {}).get("error") or {}
        except Exception:
            error = {}
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Meta token exchange failed",
                "meta_status": response.status_code,
                "meta_error": error.get("message") or "Unknown Meta OAuth error",
                "meta_type": error.get("type"),
                "meta_code": error.get("code"),
                "meta_subcode": error.get("error_subcode"),
            },
        )
    token_data = response.json()
    _connectors.save_connector(
        workspace_id=state_row["workspace_id"],
        provider="meta",
        status="connected",
        external_id=None,
        account_label="Meta account",
        secret_blob=_connectors.encrypt_json(token_data),
        metadata={
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "scope": ",".join(_connectors.META_SCOPES),
        },
    )
    return {"ok": True, "provider": "meta", "workspace_id": state_row["workspace_id"]}


_app_main.meta_authorization_url = _meta_business_authorization_url
_app_main.meta_callback = _meta_business_callback

# If the saved Meta Ad Account ID is missing or invalid (for example an email
# address was entered), discover ad accounts from the already-authorized Meta
# user token. Automatically select the account when there is exactly one.
_original_sync_meta = _connectors.sync_meta


def _valid_meta_ad_account_id(value: str) -> bool:
    raw = value.strip()
    if raw.startswith("act_"):
        raw = raw[4:]
    return bool(raw) and raw.isdigit()


async def _sync_meta_with_account_discovery(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = _connectors.get_connector(workspace_id, "meta", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect Meta before syncing")

    metadata = connector.get("metadata") or {}
    current_id = str(metadata.get("ad_account_id") or "").strip()
    if not _valid_meta_ad_account_id(current_id):
        token = _connectors.decrypt_json(connector["secret_blob"])
        access_token = token.get("access_token")
        if not access_token:
            raise HTTPException(status_code=409, detail="Meta connector has no access token")

        graph_version = (os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://graph.facebook.com/{graph_version}/me/adaccounts",
                params={
                    "access_token": access_token,
                    "fields": "id,account_id,name,account_status,currency",
                    "limit": 100,
                },
            )
        if response.status_code >= 400:
            try:
                error = (response.json() or {}).get("error") or {}
            except Exception:
                error = {}
            message = error.get("message") or f"HTTP {response.status_code}"
            code = error.get("code")
            suffix = f" (Meta code {code})" if code is not None else ""
            raise HTTPException(status_code=502, detail=f"Could not list Meta ad accounts: {message}{suffix}")

        accounts = response.json().get("data", [])
        if not accounts:
            raise HTTPException(status_code=409, detail="No Meta ad accounts were found for this Facebook login")

        if len(accounts) > 1:
            safe_accounts = [
                {
                    "id": str(account.get("id") or ""),
                    "name": str(account.get("name") or "Unnamed account"),
                    "currency": account.get("currency"),
                }
                for account in accounts[:25]
            ]
            _connectors.update_connector_metadata(workspace_id, "meta", {"available_ad_accounts": safe_accounts})
            options = "; ".join(f"{a['name']} ({a['id']})" for a in safe_accounts)
            raise HTTPException(status_code=409, detail=f"Multiple Meta ad accounts found: {options}")

        account = accounts[0]
        selected_id = str(account.get("id") or "").strip()
        if not selected_id:
            account_id = str(account.get("account_id") or "").strip()
            selected_id = f"act_{account_id}" if account_id else ""
        if not _valid_meta_ad_account_id(selected_id):
            raise HTTPException(status_code=502, detail="Meta returned an invalid ad account ID")

        _connectors.update_connector_metadata(
            workspace_id,
            "meta",
            {
                "ad_account_id": selected_id,
                "ad_account_name": account.get("name"),
                "ad_account_currency": account.get("currency"),
            },
        )

    # Preflight the exact ad-account lookup and expose only Meta's safe error
    # metadata. Never expose the access token or any application secret.
    connector = _connectors.get_connector(workspace_id, "meta", include_secret=True)
    metadata = connector.get("metadata") or {}
    ad_account = str(metadata.get("ad_account_id") or "").strip()
    if not ad_account.startswith("act_"):
        ad_account = f"act_{ad_account}"
    token = _connectors.decrypt_json(connector["secret_blob"])
    access_token = token.get("access_token")
    graph_version = (os.getenv("META_GRAPH_VERSION") or "v24.0").strip()
    async with httpx.AsyncClient(timeout=20) as client:
        probe = await client.get(
            f"https://graph.facebook.com/{graph_version}/{ad_account}",
            params={"access_token": access_token, "fields": "id,account_id,name,currency"},
        )
    if probe.status_code >= 400:
        try:
            error = (probe.json() or {}).get("error") or {}
        except Exception:
            error = {}
        message = error.get("message") or f"HTTP {probe.status_code}"
        code = error.get("code")
        subcode = error.get("error_subcode")
        parts = [f"Meta ad account lookup failed: {message}"]
        if code is not None:
            parts.append(f"code {code}")
        if subcode is not None:
            parts.append(f"subcode {subcode}")
        raise HTTPException(status_code=502, detail=" | ".join(parts))

    return await _original_sync_meta(workspace_id, days)


_connectors.sync_meta = _sync_meta_with_account_discovery
_app_main.sync_meta = _sync_meta_with_account_discovery


def _configured(name: str) -> bool:
    return bool((os.getenv(name) or "").strip())


def _database_connection_ok() -> bool:
    if not postgres_url:
        return False
    try:
        import app.store as _store

        with _store._connect() as con:
            row = con.execute("SELECT 1").fetchone()
        return bool(row and int(row[0]) == 1)
    except Exception:
        return False


def _openai_connection_ok() -> bool:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return False
    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=8.0,
        )
        return response.status_code == 200
    except Exception:
        return False


def _https_runtime() -> bool:
    return bool(os.getenv("VERCEL")) or (os.getenv("VEZMORA_APP_URL") or "").lower().startswith("https://")


def _internal_secrets_configured() -> bool:
    return all(_configured(name) for name in ("VEZMORA_APP_URL", "VEZMORA_SECRET_KEY", "CRON_SECRET"))


def _stripe_configured() -> bool:
    return all(
        _configured(name)
        for name in (
            "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_PRICE_STARTER",
            "STRIPE_PRICE_GROWTH",
            "STRIPE_PRICE_SCALE",
        )
    )


def _smtp_configured() -> bool:
    return _configured("SMTP_HOST") and _configured("SMTP_FROM")


def _google_oauth_configured() -> bool:
    return all(_configured(name) for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"))


def _meta_oauth_configured() -> bool:
    return all(_configured(name) for name in ("META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"))


@app.middleware("http")
async def production_security_headers(request, call_next):
    """Apply low-risk browser security defaults to every Vexmera response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/") or request.url.path.startswith("/health"):
        response.headers.setdefault("Cache-Control", "no-store")
    if _https_runtime():
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.get("/health/runtime")
def runtime_diagnostics() -> dict[str, object]:
    """Expose only non-secret deployment diagnostics for production debugging."""
    return {
        "ok": True,
        "brand": "Vexmera",
        "vercel": bool(os.getenv("VERCEL")),
        "vercel_env": os.getenv("VERCEL_ENV") or None,
        "git_commit_sha": os.getenv("VERCEL_GIT_COMMIT_SHA") or None,
        "database_url_configured": _configured("DATABASE_URL"),
        "postgres_url_configured": _configured("POSTGRES_URL"),
        "remote_store_configured": _configured("TURSO_DATABASE_URL"),
        "database_connection_ok": _database_connection_ok(),
        "openai_api_key_configured": _configured("OPENAI_API_KEY"),
        "openai_connection_ok": _openai_connection_ok(),
        "openai_model_configured": _configured("OPENAI_MODEL"),
        "serverless_configured": (os.getenv("VEZMORA_SERVERLESS") or "").lower() in {"1", "true", "yes", "on"},
        "app_url_configured": _configured("VEZMORA_APP_URL"),
        "app_secret_configured": _configured("VEZMORA_SECRET_KEY"),
        "cron_secret_configured": _configured("CRON_SECRET"),
        "internal_secrets_configured": _internal_secrets_configured(),
        "stripe_configured": _stripe_configured(),
        "smtp_host_configured": _configured("SMTP_HOST"),
        "smtp_port_configured": _configured("SMTP_PORT"),
        "smtp_username_configured": _configured("SMTP_USERNAME"),
        "smtp_password_configured": _configured("SMTP_PASSWORD"),
        "smtp_from_configured": _configured("SMTP_FROM"),
        "smtp_starttls_configured": _configured("SMTP_STARTTLS"),
        "smtp_configured": _smtp_configured(),
        "google_oauth_configured": _google_oauth_configured(),
        "meta_oauth_configured": _meta_oauth_configured(),
    }


__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
