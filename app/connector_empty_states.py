from __future__ import annotations

from typing import Any, Awaitable, Callable

from . import connectors as _connectors


Syncer = Callable[[int, int], Awaitable[dict[str, object]]]


_original_sync_google: Syncer = _connectors.sync_google
_original_sync_meta: Syncer = _connectors.sync_meta


def _with_empty_state_warning(provider_label: str, result: dict[str, object], days: int) -> dict[str, object]:
    """Make successful zero-row syncs explicit without turning them into failures."""
    warnings = result.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
        result["warnings"] = warnings

    try:
        campaign_rows = int(result.get("campaign_rows") or 0)
    except (TypeError, ValueError):
        campaign_rows = 0

    if campaign_rows == 0 and not any("no campaign data" in str(w).lower() for w in warnings):
        warnings.append(
            f"No campaign data found for {provider_label} in the selected {days}-day period. "
            "The connection can still be healthy; the account may have no campaigns or no activity in this period."
        )
    return result


async def sync_google_with_empty_state(workspace_id: int, days: int = 7) -> dict[str, object]:
    result = await _original_sync_google(workspace_id, days)
    result = _with_empty_state_warning("Google Ads", result, days)
    _connectors.update_connector_metadata(workspace_id, "google", {"last_sync": result})
    return result


async def sync_meta_with_empty_state(workspace_id: int, days: int = 7) -> dict[str, object]:
    result = await _original_sync_meta(workspace_id, days)
    result = _with_empty_state_warning("Meta Ads", result, days)
    _connectors.update_connector_metadata(workspace_id, "meta", {"last_sync": result})
    return result


_connectors.sync_google = sync_google_with_empty_state
_connectors.sync_meta = sync_meta_with_empty_state
