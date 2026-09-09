from __future__ import annotations

import os

from app.production_env_guards import apply_production_env_guards


_PRIVATE_BETA_DISABLED_FLAGS = (
    "VEZMORA_DEV_SHOW_TOKENS",
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
)


def test_vercel_forces_private_beta_unsafe_flags_off(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        monkeypatch.setenv(name, "true")

    apply_production_env_guards()

    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        assert os.getenv(name) == "false"


def test_local_development_flags_are_not_overridden(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        monkeypatch.setenv(name, "true")

    apply_production_env_guards()

    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        assert os.getenv(name) == "true"
