from __future__ import annotations

from scripts import pilot_preflight


def _snapshot(*, core_internal_secrets_configured: bool | None) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "phase": "private_beta",
        "private_beta_execution_safe": True,
        "production_transport_safe": True,
        "pilot_readiness": {
            "configuration_ready": True,
            "configuration_blockers": [],
            "manual_gates": [],
        },
    }
    if core_internal_secrets_configured is not None:
        snapshot["core_internal_secrets_configured"] = core_internal_secrets_configured
    return snapshot


def test_pilot_preflight_blocks_explicitly_missing_internal_secrets(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "_checkout_pricing_reconciled", lambda: True)
    monkeypatch.setattr(
        pilot_preflight,
        "beta_safety_snapshot",
        lambda: _snapshot(core_internal_secrets_configured=False),
    )

    result = pilot_preflight.build_preflight_snapshot()

    assert result["ok"] is False
    assert result["status"] == "configuration_blocked"
    assert result["core_internal_secrets_configured"] is False
    assert result["blockers"] == ["core_internal_secrets_configured"]


def test_pilot_preflight_accepts_configured_internal_secrets(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "_checkout_pricing_reconciled", lambda: True)
    monkeypatch.setattr(
        pilot_preflight,
        "beta_safety_snapshot",
        lambda: _snapshot(core_internal_secrets_configured=True),
    )

    result = pilot_preflight.build_preflight_snapshot()

    assert result["ok"] is True
    assert result["status"] == "configuration_clear"
    assert result["core_internal_secrets_configured"] is True
    assert result["blockers"] == []


def test_pilot_preflight_keeps_legacy_snapshot_compatibility(monkeypatch):
    monkeypatch.setattr(pilot_preflight, "_checkout_pricing_reconciled", lambda: True)
    monkeypatch.setattr(
        pilot_preflight,
        "beta_safety_snapshot",
        lambda: _snapshot(core_internal_secrets_configured=None),
    )

    result = pilot_preflight.build_preflight_snapshot()

    assert result["ok"] is True
    assert result["core_internal_secrets_configured"] is True
