from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from . import connectors as _connectors
from .store import (
    add_notification,
    get_connector,
    get_fx_rate,
    get_workspace_settings,
    update_connector_metadata,
    upsert_campaign_metric,
    upsert_kpi,
)

_RETRYABLE_META_STATUS = {429, 500, 502, 503, 504}
_META_RATE_LIMIT_CODES = {4, 17, 32, 613}


def _retry_delay(response: Any | None, attempt: int) -> float:
    raw = response.headers.get("Retry-After") if response is not None and getattr(response, "headers", None) else None
    if raw:
        try:
            return min(max(float(raw), 0.0), 8.0)
        except (TypeError, ValueError):
            pass
    return min(0.5 * (2**attempt), 4.0)


async def _meta_get(
    client: Any,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    max_attempts: int = 4,
) -> Any:
    """GET a Meta read endpoint with bounded retry for transient HTTP/network failures."""
    attempts = max(1, min(int(max_attempts), 6))
    response = None
    for attempt in range(attempts):
        try:
            response = await client.get(url, params=params)
        except httpx.TransportError:
            if attempt == attempts - 1:
                # Transport exceptions can include the request URL. Meta requests
                # may carry access tokens in query parameters, so never surface or
                # retain the raw exception as user-visible diagnostic context.
                raise HTTPException(
                    status_code=502,
                    detail="Meta request failed after bounded network retries",
                ) from None
            await asyncio.sleep(_retry_delay(None, attempt))
            continue

        if response.status_code not in _RETRYABLE_META_STATUS or attempt == attempts - 1:
            return response
        await asyncio.sleep(_retry_delay(response, attempt))
    return response


def _meta_error_detail(response: Any, action: str) -> str:
    """Map provider failures to actionable messages without returning raw Meta text or tokens."""
    code = None
    try:
        payload = response.json()
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            code = error.get("code")
    except Exception:
        pass

    if code == 190:
        return "Meta authorization is expired or invalid. Reconnect Meta and try again."
    if response.status_code == 429 or code in _META_RATE_LIMIT_CODES:
        return "Meta rate limit was reached after bounded retries. Try the sync again later."
    return f"{action} failed ({response.status_code})"


def _max_meta_pages() -> int:
    raw = (os.getenv("VEZMORA_META_MAX_INSIGHTS_PAGES") or "50").strip()
    try:
        return max(1, min(int(raw), 100))
    except ValueError:
        return 50


async def _meta_insight_rows(
    client: Any,
    url: str,
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Read every bounded Meta Insights page before any aggregate data is written."""
    rows: list[dict[str, Any]] = []
    next_url: str | None = url
    next_params: dict[str, Any] | None = params
    pages = 0
    seen_next: set[str] = set()
    max_pages = _max_meta_pages()

    while next_url and pages < max_pages:
        response = await _meta_get(client, next_url, params=next_params)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=_meta_error_detail(response, "Meta insights sync"))
        try:
            payload = response.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Meta insights returned an invalid response") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=502, detail="Meta insights returned an invalid response")

        page_rows = payload.get("data") or []
        if not isinstance(page_rows, list):
            raise HTTPException(status_code=502, detail="Meta insights returned an invalid data page")
        rows.extend(row for row in page_rows if isinstance(row, dict))
        pages += 1

        candidate = (payload.get("paging") or {}).get("next") if isinstance(payload.get("paging") or {}, dict) else None
        if not candidate:
            next_url = None
            break
        candidate = str(candidate)
        if candidate in seen_next:
            raise HTTPException(status_code=502, detail="Meta insights pagination returned a repeated page")
        seen_next.add(candidate)
        next_url = candidate
        # Meta's paging URL contains the cursor and its own query values. Do not
        # append the first-page params again on subsequent requests.
        next_params = None

    if next_url:
        raise HTTPException(status_code=502, detail="Meta insights exceeded the safe pagination limit")
    return rows, pages


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("date_start") or ""), str(row.get("campaign_id") or ""))
        unique[key] = row
    return list(unique.values())


async def sync_meta_reliable(workspace_id: int, days: int = 7) -> dict[str, object]:
    connector = get_connector(workspace_id, "meta", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect Meta before syncing")
    metadata = connector.get("metadata") or {}
    ad_account = str(metadata.get("ad_account_id") or "").strip()
    if not ad_account:
        raise HTTPException(status_code=409, detail="Meta ad account ID is missing")
    if not ad_account.startswith("act_"):
        ad_account = f"act_{ad_account}"

    token = _connectors.decrypt_json(connector["secret_blob"])
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=409, detail="Meta connector has no access token")

    graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
    base_currency = str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()
    start_date, end_date = _connectors._date_range(days)
    params = {
        "access_token": access_token,
        "fields": "date_start,campaign_id,campaign_name,impressions,clicks,spend,actions,action_values",
        "level": "campaign",
        "time_increment": 1,
        "time_range": json.dumps({"since": start_date, "until": end_date}),
        "limit": 100,
    }

    async with httpx.AsyncClient(timeout=40) as client:
        account_response = await _meta_get(
            client,
            f"https://graph.facebook.com/{graph_version}/{ad_account}",
            params={"access_token": access_token, "fields": "currency,name"},
        )
        if account_response.status_code >= 400:
            raise HTTPException(status_code=502, detail=_meta_error_detail(account_response, "Meta ad account lookup"))
        try:
            account_data = account_response.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Meta ad account lookup returned an invalid response") from exc
        if not isinstance(account_data, dict):
            raise HTTPException(status_code=502, detail="Meta ad account lookup returned an invalid response")

        fetched_rows, pages = await _meta_insight_rows(
            client,
            f"https://graph.facebook.com/{graph_version}/{ad_account}/insights",
            params,
        )

    rows = _dedupe_rows(fetched_rows)
    currency = str(account_data.get("currency") or base_currency).upper()
    daily: dict[str, dict[str, float]] = {}
    rate = get_fx_rate(workspace_id, currency)

    for row in rows:
        leads = _connectors._action_total(row.get("actions"), {"lead", "onsite_conversion.lead_grouped"})
        conversions = _connectors._action_total(
            row.get("actions"),
            {"purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"},
        )
        revenue = _connectors._action_total(
            row.get("action_values"),
            {"purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"},
        )
        spend = float(row.get("spend", 0) or 0)
        metric_date = str(row.get("date_start") or "")
        campaign_id = row.get("campaign_id")
        if not metric_date or campaign_id in (None, ""):
            continue

        upsert_campaign_metric(
            workspace_id,
            {
                "provider": "meta_ads",
                "external_campaign_id": campaign_id,
                "campaign_name": row.get("campaign_name") or str(campaign_id),
                "date": metric_date,
                "impressions": int(row.get("impressions", 0) or 0),
                "clicks": int(row.get("clicks", 0) or 0),
                "conversions": conversions,
                "spend": spend,
                "revenue": revenue,
                "currency": currency,
            },
        )

        if rate is not None:
            bucket = daily.setdefault(
                metric_date,
                {"impressions": 0, "clicks": 0, "leads": 0, "conversions": 0, "spend": 0.0, "revenue": 0.0},
            )
            bucket["impressions"] += int(row.get("impressions", 0) or 0)
            bucket["clicks"] += int(row.get("clicks", 0) or 0)
            bucket["leads"] += leads
            bucket["conversions"] += conversions
            bucket["spend"] += spend * rate
            bucket["revenue"] += revenue * rate

    warnings: list[str] = []
    if rate is None:
        warnings.append(
            f"Missing FX rate for Meta Ads {currency} → {base_currency}; raw campaign rows were saved but aggregate KPI was skipped"
        )

    for metric_date, bucket in daily.items():
        upsert_kpi(
            workspace_id,
            {
                "date": metric_date,
                "impressions": int(bucket["impressions"]),
                "clicks": int(bucket["clicks"]),
                "leads": int(round(bucket["leads"])),
                "conversions": int(round(bucket["conversions"])),
                "spend_sek": bucket["spend"],
                "revenue_sek": bucket["revenue"],
                "source": "meta_ads",
                "currency": base_currency,
            },
        )

    result = {
        "ads_rows": len(daily),
        "campaign_rows": len(rows),
        "insight_pages": pages,
        "account": account_data.get("name") or ad_account,
        "currency": currency,
        "base_currency": base_currency,
        "warnings": warnings,
    }
    update_connector_metadata(
        workspace_id,
        "meta",
        {"last_sync_at": datetime.now(timezone.utc).isoformat(), "last_sync": result},
    )
    add_notification(
        workspace_id,
        "sync",
        "Meta sync complete",
        f"Synced {len(rows)} daily insight rows across {pages} page(s).",
        result,
    )
    return result


def install_meta_read_reliability() -> None:
    if getattr(_connectors, "_vexmera_meta_read_reliability_installed", False):
        return
    _connectors.sync_meta = sync_meta_reliable
    _connectors._vexmera_meta_read_reliability_installed = True
