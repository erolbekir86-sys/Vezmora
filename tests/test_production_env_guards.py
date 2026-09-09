from __future__ import annotations

import os

from app.production_env_guards import apply_production_env_guards


_PRIVATE_BETA_DISABLED_FLAGS = (
    "VEZMORA_DEV_SHOW_TOKENS",
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
)


def _clear_stripe(monkeypatch):
    for name in (
        "STRIPE_PRICE_START",
        "STRIPE_PRICE_GROWTH",
        "STRIPE_PRICE_PRO",
        "STRIPE_PRICE_STARTER",
        "STRIPE_PRICE_SCALE",
        "VEZMORA_STRIPE_PRICING_VERSION",
    ):
        monkeypatch.delenv(name, raising=False)


def test_vercel_forces_private_beta_unsafe_flags_off(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        monkeypatch.setenv(name, "true")

    apply_production_env_guards()

    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        assert os.getenv(name) == "false"


def test_vercel_clears_stale_legacy_only_stripe_price_aliases(monkeypatch):
    _clear_stripe(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("STRIPE_PRICE_STARTER", "old-start")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "growth-shared-name")
    monkeypatch.setenv("STRIPE_PRICE_SCALE", "old-scale")

    apply_production_env_guards()

    assert os.getenv("STRIPE_PRICE_STARTER") is None
    assert os.getenv("STRIPE_PRICE_GROWTH") == "growth-shared-name"
    assert os.getenv("STRIPE_PRICE_SCALE") is None


def test_vercel_maps_current_prices_to_legacy_runtime_check_only_after_version_gate(monkeypatch):
    _clear_stripe(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("STRIPE_PRICE_START", "current-start")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "current-growth")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "current-pro")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", "2026-09-start-growth-pro")

    apply_production_env_guards()

    assert os.getenv("STRIPE_PRICE_STARTER") == "current-start"
    assert os.getenv("STRIPE_PRICE_GROWTH") == "current-growth"
    assert os.getenv("STRIPE_PRICE_SCALE") == "current-pro"


def test_local_development_flags_and_stripe_vars_are_not_overridden(monkeypatch):
    _clear_stripe(monkeypatch)
    monkeypatch.delenv("VERCEL", raising=False)
    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        monkeypatch.setenv(name, "true")
    monkeypatch.setenv("STRIPE_PRICE_STARTER", "legacy-local")

    apply_production_env_guards()

    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        assert os.getenv(name) == "true"
    assert os.getenv("STRIPE_PRICE_STARTER") == "legacy-local"
