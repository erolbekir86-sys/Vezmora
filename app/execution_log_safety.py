from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Any

from . import store as _store
from .secret_redaction import redact_sensitive_text

_ORIGINAL_LOG_EXECUTION = _store.log_execution


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, Mapping):
        return {str(key): _redact_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_redact_value(item) for item in value]
    return value


@wraps(_ORIGINAL_LOG_EXECUTION)
def log_execution_safely(
    workspace_id: int,
    approval_id: int,
    user_id: int | None,
    provider: str,
    action_type: str,
    request: dict[str, Any],
    result: dict[str, Any],
    status: str,
) -> int:
    """Redact credentials before execution request/result audit JSON is persisted."""
    return _ORIGINAL_LOG_EXECUTION(
        workspace_id,
        approval_id,
        user_id,
        provider,
        action_type,
        _redact_value(request),
        _redact_value(result),
        status,
    )


def install_execution_log_safety() -> None:
    """Install safe execution logging before main/autopilot bind store.log_execution."""
    if getattr(_store, "_vexmera_execution_log_safety_installed", False):
        return
    _store.log_execution = log_execution_safely
    _store._vexmera_execution_log_safety_installed = True
