"""Read-only TikTok Ads authorization and reporting preview.

The app stays disabled until its reporting-only permissions are approved. Report
totals remain separate from workspace KPIs until a live reconciliation is done.
"""
from __future__ import annotations

import os
import re
import secrets
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import HTTPException

from . import connectors

API_BASE = "https://business-api.tiktok.com/open_api/v2.0"
_ID = re.compile(r"^[0-9]{1,32}$")


def _require_configuration() -> None:
    details = connectors.connector_readiness()["tiktok"]
    if not details["configured"]:
        raise HTTPException(503, "TikTok Ads OAuth is not configured for this environment")
    if not details.get("external_approval_confirmed"):
        raise HTTPException(503, "TikTok reporting-only app approval must be confirmed before connecting")


def tiktok_authorization_url(workspace_id: int, user_id: int) -> str:
    _require_configuration()
    # Use the advertiser authorization URL supplied by My Apps, rather than
    # confusing Marketing API authorization with consumer Login Kit scopes.
    parsed = urlsplit((os.getenv("TIKTOK_AUTHORIZATION_URL") or "").strip())
    query = parse_qs(parsed.query, keep_blank_values=True)
    app_id = (os.getenv("TIKTOK_APP_ID") or "").strip()
    redirect = (os.getenv("TIKTOK_REDIRECT_URI") or "").strip()
    if (
        parsed.scheme != "https" or parsed.netloc != "business-api.tiktok.com"
        or parsed.path != "/portal/auth" or parsed.fragment
        or query.get("app_id") != [app_id] or query.get("redirect_uri") != [redirect]
        or set(query) - {"app_id", "redirect_uri", "state"}
    ):
        raise HTTPException(503, "TikTok advertiser authorization URL does not match the configured app and callback")
    state = secrets.token_urlsafe(28)
    connectors.save_oauth_state(state, user_id, workspace_id, "tiktok")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode({
        "app_id": app_id, "redirect_uri": redirect, "state": state,
    }), ""))


def _response_data(response: httpx.Response) -> dict:
    if response.status_code in {401, 403}:
        raise HTTPException(409, "TikTok authorization or reporting permission is missing; reconnect TikTok")
    if response.status_code >= 300:
        raise HTTPException(502, "TikTok request failed; retry or check the provider connection")
    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(502, "TikTok returned an invalid response") from exc
    if not isinstance(payload, dict) or type(payload.get("code")) is not int or payload["code"] != 0:
        # Provider messages can contain credentials or account information.
        raise HTTPException(502, "TikTok rejected the request; check app approval and account authorization")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise HTTPException(502, "TikTok returned an invalid response")
    return data


async def tiktok_callback(auth_code: str, state: str) -> dict[str, object]:
    _require_configuration()
    state_row = connectors.consume_oauth_state(state, "tiktok")
    if not state_row:
        raise HTTPException(400, "Invalid or expired OAuth state")
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.post(f"{API_BASE}/oauth2/access_token/", json={
                "app_id": (os.getenv("TIKTOK_APP_ID") or "").strip(),
                "secret": (os.getenv("TIKTOK_APP_SECRET") or "").strip(),
                "auth_code": auth_code,
            })
    except httpx.HTTPError as exc:
        raise HTTPException(502, "TikTok token exchange could not be completed") from exc
    data = _response_data(response)
    token = data.get("access_token")
    advertisers = data.get("advertiser_ids")
    if not isinstance(token, str) or not token.strip() or len(token) > 8192:
        raise HTTPException(502, "TikTok returned no usable access token")
    if not isinstance(advertisers, list) or not advertisers or len(advertisers) > 1000:
        raise HTTPException(409, "TikTok authorization returned no usable advertiser accounts")
    ids = [str(value) for value in advertisers if not isinstance(value, bool)]
    if len(ids) != len(advertisers) or any(not _ID.fullmatch(value) for value in ids):
        raise HTTPException(502, "TikTok returned invalid advertiser accounts")
    workspace_id = state_row["workspace_id"]
    previous = connectors.get_connector(workspace_id, "tiktok") or {}
    selected = str((previous.get("metadata") or {}).get("advertiser_id") or "")
    selected = selected if selected in ids else (ids[0] if len(ids) == 1 else "")
    connectors.save_connector(
        workspace_id, "tiktok", "connected", selected or None, "TikTok Ads",
        connectors.encrypt_json({"access_token": token.strip(), "advertiser_ids": ids}),
        {"advertiser_id": selected, "read_only": True, "preview_only": True,
         "connected_at": datetime.now(timezone.utc).isoformat()},
    )
    return {"ok": True, "provider": "tiktok", "workspace_id": workspace_id}


def _number(value: object) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(502, "TikTok returned an unavailable reporting metric") from exc
    if not number.is_finite() or number < 0 or number > Decimal("1e18"):
        raise HTTPException(502, "TikTok returned an invalid reporting metric")
    return number


async def sync_tiktok(workspace_id: int, days: int = 7) -> dict[str, object]:
    _require_configuration()
    connector = connectors.get_connector(workspace_id, "tiktok", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(409, "Connect TikTok before syncing")
    token = connectors.decrypt_json(connector["secret_blob"])
    selected = str((connector.get("metadata") or {}).get("advertiser_id") or "")
    if not _ID.fullmatch(selected) or selected not in token.get("advertiser_ids", []):
        raise HTTPException(409, "Choose a TikTok Advertiser ID authorized by this connection")
    access = token.get("access_token")
    if not isinstance(access, str) or not access.strip():
        raise HTTPException(409, "TikTok access is missing; reconnect TikTok")
    start, end = connectors._date_range(min(30, max(1, days)))
    totals: dict[str, dict[str, Decimal]] = {}
    rows = 0
    warnings = ["TikTok is a reporting preview. These totals are not included in workspace KPIs or ROAS until live reconciliation is approved."]
    if days > 30:
        warnings.append("TikTok daily reporting was limited to the most recent 30 days.")
    seen: set[tuple[str, str]] = set()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            for page in range(1, 21):
                response = await client.post(f"{API_BASE}/report/integrated/get/", headers={
                    "Access-Token": access, "Content-Type": "application/json",
                }, json={
                    "advertiser_ids": [selected], "dimensions": ["campaign_id", "stat_time_day"],
                    "metrics": ["campaign_name", "currency", "impressions", "clicks", "spend"],
                    "start_date": start, "end_date": end, "page": page, "page_size": 1000,
                })
                data = _response_data(response)
                batch, info = data.get("list"), data.get("page_info")
                if not isinstance(batch, list) or not isinstance(info, dict):
                    raise HTTPException(502, "TikTok returned an invalid reporting page")
                total_pages = info.get("total_page")
                if type(total_pages) is not int or not 0 <= total_pages <= 20 or type(info.get("page")) is not int or info["page"] != page or len(batch) > 1000 or (not total_pages and batch) or (page < total_pages and not batch):
                    raise HTTPException(502, "TikTok reporting pagination is incomplete; no new report was saved")
                if data.get("extra_info"):
                    raise HTTPException(409, "TikTok reporting contains provider completeness warnings; no new report was saved")
                for row in batch:
                    if not isinstance(row, dict):
                        raise HTTPException(502, "TikTok returned an invalid reporting row")
                    dims, metrics = row.get("dimensions"), row.get("metrics")
                    if not isinstance(dims, dict) or not isinstance(metrics, dict):
                        raise HTTPException(502, "TikTok returned an invalid reporting row")
                    campaign, day = str(dims.get("campaign_id") or ""), str(dims.get("stat_time_day") or "")[:10]
                    currency = str(metrics.get("currency") or "").upper()
                    try:
                        date.fromisoformat(day)
                    except ValueError as exc:
                        raise HTTPException(502, "TikTok returned an invalid report date") from exc
                    if not _ID.fullmatch(campaign) or not start <= day <= end or not re.fullmatch(r"[A-Z]{3}", currency) or (campaign, day) in seen:
                        raise HTTPException(502, "TikTok reporting could not be reconciled; no new report was saved")
                    seen.add((campaign, day))
                    bucket = totals.setdefault(currency, {"spend": Decimal(0), "impressions": Decimal(0), "clicks": Decimal(0)})
                    for key in bucket:
                        bucket[key] += _number(metrics.get(key))
                    rows += 1
                if page >= total_pages:
                    break
            else:
                raise HTTPException(502, "TikTok reporting page limit exceeded; no new report was saved")
    except httpx.HTTPError as exc:
        raise HTTPException(502, "TikTok reporting could not be completed; no new report was saved") from exc
    if not rows:
        warnings.append("No campaign data found for TikTok Ads in this period.")
    result = {
        "report_rows": rows, "preview_only": True, "read_only": True,
        "date_range": {"start": start, "end": end}, "warnings": warnings,
        "totals_by_currency": {currency: {key: float(value) for key, value in bucket.items()} for currency, bucket in totals.items()},
    }
    connectors.update_connector_metadata(workspace_id, "tiktok", {
        "last_sync_at": datetime.now(timezone.utc).isoformat(), "last_sync": result,
    })
    return result
