from __future__ import annotations

from app.production_env_guards import apply_production_env_guards


def test_vercel_forces_development_token_responses_off(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VEZMORA_DEV_SHOW_TOKENS", "true")

    apply_production_env_guards()

    assert monkeypatch.getenv("VEZMORA_DEV_SHOW_TOKENS") == "false"


def test_local_development_flag_is_not_overridden(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_DEV_SHOW_TOKENS", "true")

    apply_production_env_guards()

    assert monkeypatch.getenv("VEZMORA_DEV_SHOW_TOKENS") == "true"
