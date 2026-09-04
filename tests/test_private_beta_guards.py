from __future__ import annotations

from app.autopilot import autopilot_runtime_enabled
from app.execution import execution_enabled


def test_external_execution_is_off_by_default(monkeypatch):
    """Private beta must never execute external ad changes by default."""
    monkeypatch.delenv("VEZMORA_EXECUTION_ENABLED", raising=False)
    assert execution_enabled() is False


def test_autopilot_execution_is_off_by_default(monkeypatch):
    """Autopilot execution requires a separate explicit runtime opt-in."""
    monkeypatch.delenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", raising=False)
    assert autopilot_runtime_enabled() is False


def test_truthy_values_are_explicit(monkeypatch):
    """Only known truthy values may unlock the execution gates."""
    monkeypatch.setenv("VEZMORA_EXECUTION_ENABLED", "false")
    monkeypatch.setenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", "false")
    assert execution_enabled() is False
    assert autopilot_runtime_enabled() is False

    monkeypatch.setenv("VEZMORA_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("VEZMORA_AUTOPILOT_EXECUTION_ENABLED", "true")
    assert execution_enabled() is True
    assert autopilot_runtime_enabled() is True
