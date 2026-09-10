from __future__ import annotations

from functools import wraps
from typing import Any

from . import store as _store

_ORIGINAL_RECORD_BILLING_EVENT = _store.record_billing_event
_SAFE_METADATA_KEYS = frozenset({"workspace_id", "plan", "trial_days"})
_SAFE_OBJECT_KEYS = frozenset({"id", "object", "status"})


def minimal_billing_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep only non-customer audit fields needed to understand a processed event."""
    safe: dict[str, Any] = {
        "id": str(payload.get("id") or ""),
        "type": str(payload.get("type") or ""),
    }
    if isinstance(payload.get("created"), (int, float)):
        safe["created"] = payload["created"]
    if isinstance(payload.get("livemode"), bool):
        safe["livemode"] = payload["livemode"]

    data = payload.get("data")
    obj = data.get("object") if isinstance(data, dict) else None
    if isinstance(obj, dict):
        safe_obj = {key: obj[key] for key in _SAFE_OBJECT_KEYS if key in obj and obj[key] is not None}
        metadata = obj.get("metadata")
        if isinstance(metadata, dict):
            safe_metadata = {
                key: str(metadata[key])
                for key in _SAFE_METADATA_KEYS
                if key in metadata and metadata[key] is not None
            }
            if safe_metadata:
                safe_obj["metadata"] = safe_metadata
        if safe_obj:
            safe["data"] = {"object": safe_obj}
    return safe


@wraps(_ORIGINAL_RECORD_BILLING_EVENT)
def record_billing_event_minimized(
    workspace_id: int | None,
    provider_event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    return _ORIGINAL_RECORD_BILLING_EVENT(
        workspace_id,
        provider_event_id,
        event_type,
        minimal_billing_event_payload(payload),
    )


def install_billing_event_minimization() -> None:
    """Minimize future Stripe audit rows before stripe_billing binds the store helper.

    This is forward-only. Historical billing-event rows are not read, rewritten or
    deleted by this guard, and the in-memory verified webhook remains unchanged for
    the billing state transition that follows.
    """
    if getattr(_store, "_vexmera_billing_event_minimization_installed", False):
        return

    _store.record_billing_event = record_billing_event_minimized
    _store._vexmera_billing_event_minimization_installed = True
