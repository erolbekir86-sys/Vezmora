from __future__ import annotations

import asyncio
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
    save_connector,
    update_connector_metadata,
    upsert_campaign_metric,
    upsert_kpi,
)

_RETRYABLE_GOOGLE_STATUS = {429, 500, 502, 503, 504}


def _retry_delay(response: Any, attempt: int) -> float:
    raw = response.headers.get("Retry-After") if getattr(response, "headers", None) else None
    if raw:
        try:
            return min(max(float(raw), 0.0), 8.0)
        except (TypeError, ValueError):
            pass
    return min(0.5 * (2**attempt), 4.0)


async def _google_post(
    client: Any,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: object | None = None,
    data: dict[str, object] | None = None,
    max_attempts: int = 4,
) -> Any:
    """POST a Google read/token endpoint with bounded retry for transient responses."""
    attempts = max(1, min(int(max_attempts), 6))
    response = None
    for attempt in range(attempts):
        response = await client.post(url, headers=headers, json=json_body, data=data)
        if response.status_code not in _RETRYABLE_GOOGLE_STATUS or attempt == attempts - 1:
            return response
        await asyncio.sleep(_retry_delay(response, attempt))
    return response


def _safe_dict_payload(response: Any) -> dict[str, object] | None:
    try:
        payload = response.json()
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _safe_ads_results(response: Any) -> list[dict[str, object]] | None:
    try:
        batches = response.json()
    except Exception:
        return None
    if not isinstance(batches, list):
        return None

    rows: list[dict[str, object]] = []
    for batch in batches:
        if not isinstance(batch, dict):
            return None
        results = batch.get("results", [])
        if not isinstance(results, list):
            return None
        if any(not isinstance(row, dict) for row in results):
            return None
        rows.extend(results)
    return rows


def _number(value: object, default: float = 0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


async def refresh_google_access_token_reliable(workspace_id: int, connector: dict) -> tuple[str, dict]:
    """Refresh Google OAuth access with bounded retry while preserving existing fallback behavior."""
    if not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Google is not connected")

    token = _connectors.decrypt_json(connector["secret_blob"])
    refresh_token = token.get("refresh_token")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if refresh_token and client_id and client_secret:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await _google_post(
                    client,
                    _connectors.GOOGLE_TOKEN_URL,
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
        except httpx.TransportError as exc:
            if not token.get("access_token"):
                raise HTTPException(status_code=502, detail="Google access-token refresh failed") from exc
        else:
            if response.status_code < 400:
                refreshed = _safe_dict_payload(response)
                if refreshed is None:
                    if not token.get("access_token"):
                        raise HTTPException(status_code=502, detail="Google access-token refresh returned an invalid response")
                elif refreshed.get("access_token"):
                    token.update(refreshed)
                    token["refresh_token"] = refresh_token
                    save_connector(
                        workspace_id,
                        "google",
                        connector.get("status", "connected"),
                        connector.get("external_id"),
                        connector.get("account_label"),
                        _connectors.encrypt_json(token),
                        connector.get("metadata") or {},
                    )
                elif not token.get("access_token"):
                    raise HTTPException(status_code=502, detail="Google access-token refresh returned no access token")
            elif not token.get("access_token"):
                raise HTTPException(status_code=502, detail="Google access-token refresh failed")

    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=409, detail="Google connector has no access token")
    return str(access_token), token


async def sync_google_reliable(workspace_id: int, days: int = 7) -> dict[str, object]:
    """Read Google Analytics and Ads with bounded retry and fail-closed payload validation."""
    connector = get_connector(workspace_id, "google", include_secret=True)
    if not connector or connector.get("status") != "connected":
        raise HTTPException(status_code=409, detail="Connect Google before syncing")

    metadata = connector.get("metadata") or {}
    access_token, _ = await refresh_google_access_token_reliable(workspace_id, connector)
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    start_date, end_date = _connectors._date_range(days)
    base_currency = str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()
    synced: dict[str, object] = {
        "analytics_rows": 0,
        "ads_rows": 0,
        "campaign_rows": 0,
        "base_currency": base_currency,
        "warnings": [],
    }
    warnings: list[str] = synced["warnings"]  # type: ignore[assignment]

    property_id = str(metadata.get("analytics_property_id") or "").replace("properties/", "")
    if property_id:
        payload = {
            "dimensions": [{"name": "date"}],
            "metrics": [{"name": "sessions"}, {"name": "keyEvents"}, {"name": "purchaseRevenue"}],
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "currencyCode": base_currency,
            "limit": "100",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await _google_post(
                    client,
                    f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
                    headers=headers,
                    json_body=payload,
                )
        except httpx.TransportError:
            warnings.append("Analytics sync failed after bounded network retries")
        else:
            if response.status_code < 400:
                analytics_payload = _safe_dict_payload(response)
                rows = analytics_payload.get("rows", []) if analytics_payload is not None else None
                if not isinstance(rows, list):
                    warnings.append("Analytics sync returned an invalid response")
                else:
                    malformed = False
                    for row in rows:
                        if not isinstance(row, dict):
                            malformed = True
                            continue
                        dimensions = row.get("dimensionValues")
                        metrics = row.get("metricValues")
                        if not isinstance(dimensions, list) or not dimensions or not isinstance(dimensions[0], dict):
                            malformed = True
                            continue
                        if not isinstance(metrics, list) or len(metrics) < 3 or any(not isinstance(item, dict) for item in metrics[:3]):
                            malformed = True
                            continue

                        metric_date = str(dimensions[0].get("value") or "")
                        if len(metric_date) == 8 and metric_date.isdigit():
                            metric_date = f"{metric_date[:4]}-{metric_date[4:6]}-{metric_date[6:]}"
                        if not metric_date:
                            malformed = True
                            continue

                        values = [str(item.get("value") or "0") for item in metrics[:3]]
                        upsert_kpi(
                            workspace_id,
                            {
                                "date": metric_date,
                                "impressions": 0,
                                "clicks": int(_number(values[0])),
                                "leads": 0,
                                "conversions": int(_number(values[1])),
                                "spend_sek": 0,
                                "revenue_sek": _number(values[2]),
                                "source": "google_analytics",
                                "currency": base_currency,
                            },
                        )
                        synced["analytics_rows"] = int(synced["analytics_rows"]) + 1
                    if malformed:
                        warnings.append("Analytics returned malformed rows; invalid rows were skipped")
            else:
                warnings.append(f"Analytics sync failed ({response.status_code})")
    else:
        warnings.append("Google Analytics property ID is missing")

    customer_id = "".join(ch for ch in str(metadata.get("ads_customer_id") or "") if ch.isdigit())
    developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    if customer_id and developer_token:
        api_version = os.getenv("GOOGLE_ADS_API_VERSION", "v25")
        query = (
            "SELECT segments.date, customer.currency_code, campaign.id, campaign.name, "
            "metrics.impressions, metrics.clicks, metrics.conversions, metrics.conversions_value, metrics.cost_micros "
            f"FROM campaign WHERE segments.date BETWEEN '{start_date}' AND '{end_date}' ORDER BY segments.date"
        )
        ads_headers = {**headers, "developer-token": developer_token}
        login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        if login_customer_id:
            ads_headers["login-customer-id"] = "".join(ch for ch in login_customer_id if ch.isdigit())

        try:
            async with httpx.AsyncClient(timeout=40) as client:
                response = await _google_post(
                    client,
                    f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}/googleAds:searchStream",
                    headers=ads_headers,
                    json_body={"query": query},
                )
        except httpx.TransportError:
            warnings.append("Google Ads sync failed after bounded network retries")
        else:
            if response.status_code < 400:
                results = _safe_ads_results(response)
                if results is None:
                    warnings.append("Google Ads sync returned an invalid response")
                else:
                    daily: dict[str, dict[str, float]] = {}
                    for result in results:
                        segments = result.get("segments") if isinstance(result.get("segments"), dict) else {}
                        metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
                        customer = result.get("customer") if isinstance(result.get("customer"), dict) else {}
                        campaign = result.get("campaign") if isinstance(result.get("campaign"), dict) else {}
                        metric_date = str(segments.get("date") or "")
                        campaign_id = campaign.get("id")
                        if not metric_date or campaign_id in (None, ""):
                            continue

                        currency = str(customer.get("currencyCode") or customer.get("currency_code") or base_currency).upper()
                        spend = _number(metrics.get("costMicros", metrics.get("cost_micros", 0))) / 1_000_000
                        revenue = _number(metrics.get("conversionsValue", metrics.get("conversions_value", 0)))
                        conversions = _number(metrics.get("conversions", 0))
                        impressions = int(_number(metrics.get("impressions", 0)))
                        clicks = int(_number(metrics.get("clicks", 0)))

                        upsert_campaign_metric(
                            workspace_id,
                            {
                                "provider": "google_ads",
                                "external_campaign_id": campaign_id,
                                "campaign_name": campaign.get("name") or str(campaign_id),
                                "date": metric_date,
                                "impressions": impressions,
                                "clicks": clicks,
                                "conversions": conversions,
                                "spend": spend,
                                "revenue": revenue,
                                "currency": currency,
                            },
                        )
                        synced["campaign_rows"] = int(synced["campaign_rows"]) + 1

                        rate = get_fx_rate(workspace_id, currency)
                        if rate is None:
                            warning = (
                                f"Missing FX rate for Google Ads {currency} → {base_currency}; "
                                "raw campaign rows were saved but aggregate KPI was skipped"
                            )
                            if warning not in warnings:
                                warnings.append(warning)
                            continue

                        bucket = daily.setdefault(
                            metric_date,
                            {"impressions": 0, "clicks": 0, "conversions": 0, "spend": 0.0, "revenue": 0.0},
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
                                "source": "google_ads",
                                "currency": base_currency,
                            },
                        )
                        synced["ads_rows"] = int(synced["ads_rows"]) + 1
            else:
                warnings.append(f"Google Ads sync failed ({response.status_code})")
    elif customer_id:
        warnings.append("GOOGLE_ADS_DEVELOPER_TOKEN is missing")
    else:
        warnings.append("Google Ads customer ID is missing")

    update_connector_metadata(
        workspace_id,
        "google",
        {"last_sync_at": datetime.now(timezone.utc).isoformat(), "last_sync": synced},
    )
    add_notification(
        workspace_id,
        "sync",
        "Google sync complete",
        f"Analytics rows: {synced['analytics_rows']}, Ads rows: {synced['ads_rows']}",
        synced,
    )
    return synced


def install_google_read_reliability() -> None:
    if getattr(_connectors, "_vexmera_google_read_reliability_installed", False):
        return
    _connectors._refresh_google_access_token = refresh_google_access_token_reliable
    _connectors.sync_google = sync_google_reliable
    _connectors._google_read_post = _google_post
    _connectors._vexmera_google_read_reliability_installed = True
