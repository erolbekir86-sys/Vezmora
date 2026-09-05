from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app import autopilot, execution


def _approved_google_action() -> dict[str, object]:
    return {
        "id": 1,
        "status": "approved",
        "action_type": "google.pause_campaign",
        "provider": "google",
        "risk_level": "high",
        "payload": {"campaign_id": "123456789"},
    }


def test_external_execution_is_off_by_default_and_blocks_before_adapter(monkeypatch):
    monkeypatch.delenv("VEZMORA_EXECUTION_ENABLED", raising=False)
    called = False

    async def should_never_execute(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("external adapter must not run while execution is disabled")

    monkeypatch.setattr(execution, "_execute_google", should_never_execute)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(execution.execute_approved_action(1, _approved_google_action()))

    assert exc.value.status_code == 409
    assert "External execution is disabled" in str(exc.value.detail)
    assert called is False


def test_autopilot_execution_is_off_by_default(monkeypatch):
    monkeypatch.delenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", raising=False)
    monkeypatch.delenv("VEZMORA_EXECUTION_ENABLED", raising=False)

    result = asyncio.run(autopilot.run_autopilot_once(1))

    assert result == {
        "executed": 0,
        "skipped": 0,
        "disabled": True,
        "reason": "VEZMORA_AUTOPILOT_EXECUTION_ENABLED is off",
    }


def test_autopilot_still_blocks_when_only_autopilot_flag_is_enabled(monkeypatch):
    monkeypatch.setenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", "true")
    monkeypatch.delenv("VEZMORA_EXECUTION_ENABLED", raising=False)

    result = asyncio.run(autopilot.run_autopilot_once(1))

    assert result == {
        "executed": 0,
        "skipped": 0,
        "disabled": True,
        "reason": "VEZMORA_EXECUTION_ENABLED is off",
    }
