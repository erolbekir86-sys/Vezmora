from __future__ import annotations

import base64
import hashlib
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
            "notes": "Read-only sync. Analytics needs a property ID; Google Ads needs customer ID + developer token.",
        },
        "meta": {
            "label": "Meta Ads",
            "configured": bool(os.getenv("META_APP_ID") and os.getenv("META_APP_SECRET") and os.getenv("META_REDIRECT_URI")),
            "requirements": ["META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"],
            "notes": "Ads insights by default. ads_management is requested only when VEZMORA_ENABLE_META_EXECUTION_SCOPE=true.",
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


def save_connector_settings(workspace_id: int, settings: dict[str, str | None]) -> None:
    google_updates = {k: settings.get(k) for k in ("analytics_property_id", "ads_customer_id") if settings.get(k)}
    meta_updates = {"ad_account_id": settings.get("meta_ad_account_id")} if settings.get("meta_ad_account_id") else {}
    if google_updates:
        update_connector_metadata(workspace_id, "google", google_updates)
    if meta_updates:
        update_connector_metadata(workspace_id, "meta", meta_updates)


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
        synced["warnings"].append("Google Analytics property ID is missing")

    customer_id = "".join(ch for ch in str(metadata.get("ads_customer_id") or "") if ch.isdigit())
    developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    if customer_id and developer_token:
        api_version = os.getenv("GOOGLE_ADS_API_VERSION", "v25")
        query = f"""SELECT segments.date, customer.currency_code, campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.conversions, metrics.conversions_value, metrics.cost_micros FROM campaign WHERE segments.date BETWEEN '{start_date}' AND '{end_date}' ORDER BY segments.date"""
        ads_headers = {**headers, "developer-token": developer_token}
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
    elif customer_id:
        synced["warnings"].append("GOOGLE_ADS_DEVELOPER_TOKEN is missing")
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
    for provider, syncer in (("google", sync_google), ("meta", sync_meta)):
        try:
            results[provider] = await syncer(workspace_id, days)
        except HTTPException as exc:
            results[provider] = {"error": str(exc.detail), "status": exc.status_code}
        except Exception as exc:
            results[provider] = {"error": type(exc).__name__}
    return results
