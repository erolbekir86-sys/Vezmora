from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import AutopilotSettings


ACTIONS = [
    "google.pause_campaign",
    "google.enable_campaign",
    "google.set_daily_budget",
    "meta.pause_campaign",
    "meta.activate_campaign",
]


def test_autopilot_allowed_actions_accepts_all_supported_actions_once() -> None:
    settings = AutopilotSettings(allowed_actions=ACTIONS)
    assert settings.allowed_actions == ACTIONS


def test_autopilot_allowed_actions_rejects_more_than_supported_action_count() -> None:
    with pytest.raises(ValidationError):
        AutopilotSettings(allowed_actions=ACTIONS + ["google.pause_campaign"])


def test_autopilot_allowed_actions_keeps_safe_empty_default() -> None:
    assert AutopilotSettings().allowed_actions == []
