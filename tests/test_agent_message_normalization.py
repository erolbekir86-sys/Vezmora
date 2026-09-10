from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import AgentRequest


def test_agent_message_trims_surrounding_whitespace() -> None:
    request = AgentRequest(message="  Vad ska vi prioritera?  ")
    assert request.message == "Vad ska vi prioritera?"


def test_agent_message_rejects_whitespace_only_input() -> None:
    with pytest.raises(ValidationError):
        AgentRequest(message="   \t\n  ")


def test_agent_message_applies_min_length_after_trimming() -> None:
    with pytest.raises(ValidationError):
        AgentRequest(message="  x  ")
