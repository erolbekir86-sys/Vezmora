from __future__ import annotations

from typing import Awaitable, Callable

from . import connectors as _connectors


Syncer = Callable[[int, int], Awaitable[dict[str, object]]]


_original_sync_google: Syncer = _connectors.sync_google
_original_sync_meta: Syncer = _connectors.sync_meta


def _row_count(result: dict[str, object], key: str) -> int:
    """Return a safe non-negative row count for provider sync metadata."""
    try:
        return max(0, int(result.get(key) or 0))
    except (TypeError, ValueError):
        return 0


def _is_error_result(result: dict[str, object]) -> bool:
    """Avoid presenting a provider failure as a healthy empty account."""
    if result.get("error"):
        return True
    if result.get("ok") is False or result.get("success") is False:
        return True
    try:
        status = int(result.get("status") or 0)
    except (TypeError, ValueError):
        return False
    return status >= 400


def _with_empty_state_warning(provider_label: str, result: dict[str, object], days: int) -> dict[str, object]:
    """Make successful zero-row syncs explicit without turning failures into empty states."""
    if _is_error_result(result):
        return result

    raw_warnings = result.get("warnings")
    if isinstance(raw_warnings, list):
        warnings = raw_warnings
    elif raw_warnings in (None, ""):
        warnings = []
        result["warnings"] = warnings
    else:
        warnings = [str(raw_warnings)]
        result["warnings"] = warnings

    campaign_rows = _row_count(result, "campaign_rows")
    ads_rows = _row_count(result, "ads_rows")
    has_provider_rows = campaign_rows > 0 or ads_rows > 0

    if not has_provider_rows and not any("no campaign data" in str(w).lower() for w in warnings):
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
