from __future__ import annotations

import json

from scripts import pilot_preflight


def test_pilot_preflight_surfaces_checkout_pricing_gate(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "CHECKOUT_PRICING_RECONCILED", False)

    result = pilot_preflight.build_preflight_snapshot()

    assert result["checkout_pricing_reconciled"] is False
    assert "checkout_pricing_reconciliation" in result["blockers"]
    assert result["ok"] is False
    assert result["status"] == "configuration_blocked"


def test_pilot_preflight_does_not_duplicate_pricing_blocker(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "CHECKOUT_PRICING_RECONCILED", False)

    original_snapshot = pilot_preflight.beta_safety_snapshot

    def fake_snapshot():
        snapshot = original_snapshot()
        snapshot["pilot_readiness"] = dict(snapshot["pilot_readiness"])
        snapshot["pilot_readiness"]["configuration_blockers"] = [
            *snapshot["pilot_readiness"]["configuration_blockers"],
            "checkout_pricing_reconciliation",
        ]
        return snapshot

    monkeypatch.setattr(pilot_preflight, "beta_safety_snapshot", fake_snapshot)
    result = pilot_preflight.build_preflight_snapshot()

    assert result["blockers"].count("checkout_pricing_reconciliation") == 1


def test_pilot_preflight_cannot_be_mistaken_for_pilot_approval(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "CHECKOUT_PRICING_RECONCILED", True)

    original_snapshot = pilot_preflight.beta_safety_snapshot

    def fake_snapshot():
        snapshot = original_snapshot()
        snapshot["core_internal_secrets_configured"] = True
        snapshot["pilot_readiness"] = dict(snapshot["pilot_readiness"])
        snapshot["pilot_readiness"]["configuration_blockers"] = []
        snapshot["pilot_readiness"]["configuration_ready"] = True
        return snapshot

    monkeypatch.setattr(pilot_preflight, "beta_safety_snapshot", fake_snapshot)
    result = pilot_preflight.build_preflight_snapshot()

    assert result["ok"] is True
    assert result["ok_scope"] == "configuration_only"
    assert result["status"] == "manual_verification_required"
    assert result["pilot_ready"] is None
    assert result["manual_verification_required"] is bool(result["manual_gates"])
    assert "ok=true does not mean pilot-ready" in result["note"]


def test_pilot_preflight_status_can_report_configuration_clear(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "CHECKOUT_PRICING_RECONCILED", True)

    def fake_snapshot():
        return {
            "phase": "private_beta",
            "private_beta_execution_safe": True,
            "production_transport_safe": True,
            "pilot_readiness": {
                "configuration_ready": True,
                "configuration_blockers": [],
                "manual_gates": [],
            },
        }

    monkeypatch.setattr(pilot_preflight, "beta_safety_snapshot", fake_snapshot)
    result = pilot_preflight.build_preflight_snapshot()

    assert result["ok"] is True
    assert result["manual_verification_required"] is False
    assert result["status"] == "configuration_clear"
    assert result["pilot_ready"] is None


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
