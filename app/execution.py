from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import HTTPException

from .connectors import _refresh_google_access_token, decrypt_json
from .store import get_connector

SUPPORTED_ACTIONS = {
    "google.pause_campaign",
    "google.enable_campaign",
    "google.set_daily_budget",
    "meta.pause_campaign",
    "meta.activate_campaign",
}


def execution_enabled() -> bool:
    return os.getenv("VEZMORA_EXECUTION_ENABLED", "0").lower() in {"1", "true", "yes", "on"}


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def validate_action(approval: dict[str, Any]) -> dict[str, Any]:
    action_type = str(approval.get("action_type") or "")
    payload = approval.get("payload") or {}
    if action_type not in SUPPORTED_ACTIONS:
        raise HTTPException(status_code=422, detail=f"Action type is not executable in Vezmora 0.5: {action_type}")
    campaign_id = str(payload.get("campaign_id") or "").strip()
    if not campaign_id:
        raise HTTPException(status_code=422, detail="Executable actions require payload.campaign_id")
    preview = {
        "action_type": action_type,
        "provider": action_type.split(".", 1)[0],
        "campaign_id": campaign_id,
        "changes": {},
        "execution_enabled": execution_enabled(),
        "requires_explicit_confirm": True,
    }
    if action_type.endswith("pause_campaign"):
        preview["changes"] = {"status": "PAUSED"}
    elif action_type.endswith("enable_campaign") or action_type.endswith("activate_campaign"):
        preview["changes"] = {"status": "ENABLED" if action_type.startswith("google") else "ACTIVE"}
    elif action_type == "google.set_daily_budget":
        amount = payload.get("daily_budget")
        if amount is None or float(amount) <= 0:
            raise HTTPException(status_code=422, detail="google.set_daily_budget requires a positive payload.daily_budget")
        preview["changes"] = {"daily_budget": float(amount), "currency": str(payload.get("currency") or "account currency")}
    return preview


async def _google_headers(workspace_id: int) -> tuple[dict[str, str], str, dict[str, Any]]:
    connector = get_connector(workspace_id, "google", include_secret=True)
    if not connector or connector.get("status") != "connected":
        raise HTTPException(status_code=409, detail="Connect Google before executing Google Ads actions")
    metadata = connector.get("metadata") or {}
    customer_id = _digits(metadata.get("ads_customer_id"))
    developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    if not customer_id or not developer_token:
        raise HTTPException(status_code=409, detail="Google Ads customer ID and developer token are required")
    access_token, _ = await _refresh_google_access_token(workspace_id, connector)
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "developer-token": developer_token}
    login_customer_id = _digits(os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"))
    if login_customer_id:
        headers["login-customer-id"] = login_customer_id
    return headers, customer_id, metadata


async def _google_campaign_state(workspace_id: int, campaign_id: str) -> dict[str, Any]:
    headers, customer_id, _ = await _google_headers(workspace_id)
    api_version = os.getenv("GOOGLE_ADS_API_VERSION", "v25")
    cid = _digits(campaign_id)
    query = f"SELECT campaign.id, campaign.name, campaign.status, campaign.campaign_budget, campaign_budget.amount_micros FROM campaign WHERE campaign.id = {cid} LIMIT 1"
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}/googleAds:search",
            headers=headers,
            json={"query": query},
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Google Ads campaign lookup failed ({res.status_code})")
    results = res.json().get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="Google Ads campaign not found")
    row = results[0]
    campaign = row.get("campaign", {})
    budget = row.get("campaignBudget", row.get("campaign_budget", {}))
    return {
        "campaign_id": str(campaign.get("id") or cid),
        "name": campaign.get("name"),
        "status": campaign.get("status"),
        "campaign_resource": campaign.get("resourceName") or campaign.get("resource_name") or f"customers/{customer_id}/campaigns/{cid}",
        "budget_resource": campaign.get("campaignBudget") or campaign.get("campaign_budget"),
        "daily_budget": float(budget.get("amountMicros", budget.get("amount_micros", 0)) or 0) / 1_000_000,
    }


async def preview_external(workspace_id: int, approval: dict[str, Any]) -> dict[str, Any]:
    preview = validate_action(approval)
    if preview["provider"] == "google":
        try:
            preview["current"] = await _google_campaign_state(workspace_id, preview["campaign_id"])
        except HTTPException as exc:
            preview["current_lookup_error"] = str(exc.detail)
    elif preview["provider"] == "meta":
        connector = get_connector(workspace_id, "meta")
        preview["connected"] = bool(connector and connector.get("status") == "connected")
    return preview


async def _execute_google(workspace_id: int, approval: dict[str, Any]) -> dict[str, Any]:
    preview = validate_action(approval)
    headers, customer_id, _ = await _google_headers(workspace_id)
    api_version = os.getenv("GOOGLE_ADS_API_VERSION", "v25")
    action_type = approval["action_type"]
    current = await _google_campaign_state(workspace_id, preview["campaign_id"])
    if action_type in {"google.pause_campaign", "google.enable_campaign"}:
        body = {
            "operations": [{
                "update": {"resourceName": current["campaign_resource"], "status": "PAUSED" if action_type.endswith("pause_campaign") else "ENABLED"},
                "updateMask": "status",
            }],
            "partialFailure": False,
            "validateOnly": False,
        }
        endpoint = f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}/campaigns:mutate"
    else:
        budget_resource = current.get("budget_resource")
        if not budget_resource:
            raise HTTPException(status_code=409, detail="Campaign budget resource could not be resolved")
        amount_micros = int(round(float(approval["payload"]["daily_budget"]) * 1_000_000))
        body = {
            "operations": [{
                "update": {"resourceName": budget_resource, "amountMicros": str(amount_micros)},
                "updateMask": "amount_micros",
            }],
            "partialFailure": False,
            "validateOnly": False,
        }
        endpoint = f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}/campaignBudgets:mutate"
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(endpoint, headers=headers, json=body)
    if res.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Google Ads mutation failed ({res.status_code})")
    return {"provider": "google", "status": "executed", "before": current, "response": res.json()}


async def _execute_meta(workspace_id: int, approval: dict[str, Any]) -> dict[str, Any]:
    connector = get_connector(workspace_id, "meta", include_secret=True)
    if not connector or connector.get("status") != "connected" or not connector.get("secret_blob"):
        raise HTTPException(status_code=409, detail="Connect Meta before executing Meta actions")
    if "ads_management" not in str((connector.get("metadata") or {}).get("scope") or ""):
        raise HTTPException(status_code=409, detail="Meta connection needs ads_management permission. Reconnect Meta with execution scope enabled.")
    token = decrypt_json(connector["secret_blob"])
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=409, detail="Meta access token is missing")
    action_type = approval["action_type"]
    status = "PAUSED" if action_type == "meta.pause_campaign" else "ACTIVE"
    graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
    campaign_id = str((approval.get("payload") or {}).get("campaign_id") or "")
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"https://graph.facebook.com/{graph_version}/{campaign_id}",
            data={"access_token": access_token, "status": status},
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Meta campaign mutation failed ({res.status_code})")
    return {"provider": "meta", "status": "executed", "campaign_id": campaign_id, "new_status": status, "response": res.json()}


async def execute_approved_action(workspace_id: int, approval: dict[str, Any]) -> dict[str, Any]:
    if not execution_enabled():
        raise HTTPException(status_code=409, detail="External execution is disabled. Set VEZMORA_EXECUTION_ENABLED=true after reviewing the safety controls.")
    validate_action(approval)
    if approval.get("status") != "approved":
        raise HTTPException(status_code=409, detail="Only approved Queue actions can be executed")
    if str(approval["action_type"]).startswith("google."):
        return await _execute_google(workspace_id, approval)
    if str(approval["action_type"]).startswith("meta."):
        return await _execute_meta(workspace_id, approval)
    raise HTTPException(status_code=422, detail="Unsupported execution provider")
