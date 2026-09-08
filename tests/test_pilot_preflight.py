from __future__ import annotations

import json

from scripts import pilot_preflight


def test_pilot_preflight_surfaces_checkout_pricing_gate(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "CHECKOUT_PRICING_RECONCILED", False)

    result = pilot_preflight.build_preflight_snapshot()

    assert result["checkout_pricing_reconciled"] is False
    assert "checkout_pricing_reconciliation" in result["blockers"]
    assert result["ok"] is False


def test_pilot_preflight_does_not_duplicate_pricing_blocker(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "CHECKOUT_PRICING_RECONCILED", False)

    result = pilot_preflight.build_preflight_snapshot()

    assert result["blockers"].count("checkout_pricing_reconciliation") == 1


def test_pilot_preflight_never_renders_secret_values(monkeypatch):
    secret_values = {
        "VEZMORA_SECRET_KEY": "private-secret-value",
        "CRON_SECRET": "private-cron-value",
        "STRIPE_SECRET_KEY": "sk_test_private_value",
        "GOOGLE_CLIENT_SECRET": "google-private-value",
        "META_APP_SECRET": "meta-private-value",
    }
    for name, value in secret_values.items():
        monkeypatch.setenv(name, value)

    rendered = json.dumps(pilot_preflight.build_preflight_snapshot(), sort_keys=True)

    for value in secret_values.values():
        assert value not in rendered
