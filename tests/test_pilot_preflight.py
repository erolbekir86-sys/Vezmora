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


def _safe_beta_readiness_payload() -> dict[str, object]:
    return {
        "private_beta_execution_safe": True,
        "external_execution_enabled": False,
        "autopilot_execution_enabled": False,
        "meta_execution_scope_enabled": False,
        "dev_show_tokens_enabled": False,
    }


def test_live_preflight_passes_safe_public_endpoints(monkeypatch):
    responses = {
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(_safe_beta_readiness_payload())),
        "https://vexmera.com/privacy": (
            200,
            "<h1>Integritetspolicy</h1> Google API Services User Data Policy",
        ),
        "https://vexmera.com/terms": (200, "<h1>Terms of Service</h1> Vexmera"),
    }
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com/")

    assert result["ok"] is True
    assert result["blockers"] == []
    beta = result["checks"]["beta_readiness"]
    assert beta["external_execution_enabled"] is False
    assert beta["autopilot_execution_enabled"] is False
    assert beta["meta_execution_scope_enabled"] is False
    assert beta["dev_show_tokens_enabled"] is False


def test_live_preflight_blocks_if_execution_is_not_locked(monkeypatch):
    unsafe_payload = _safe_beta_readiness_payload()
    unsafe_payload.update(
        {
            "private_beta_execution_safe": False,
            "external_execution_enabled": True,
        }
    )
    responses = {
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(unsafe_payload)),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "private_beta_execution_unsafe" in result["blockers"]
    assert "external_execution_not_locked" in result["blockers"]


def test_live_preflight_blocks_meta_execution_scope_and_dev_token_display(monkeypatch):
    unsafe_payload = _safe_beta_readiness_payload()
    unsafe_payload.update(
        {
            "private_beta_execution_safe": False,
            "meta_execution_scope_enabled": True,
            "dev_show_tokens_enabled": True,
        }
    )
    responses = {
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(unsafe_payload)),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "private_beta_execution_unsafe" in result["blockers"]
    assert "meta_execution_scope_not_locked" in result["blockers"]
    assert "dev_show_tokens_not_locked" in result["blockers"]


def test_live_preflight_fails_closed_when_execution_lock_fields_are_missing(monkeypatch):
    responses = {
        "https://vexmera.com/health/beta-readiness": (
            200,
            json.dumps(
                {
                    "private_beta_execution_safe": True,
                    "external_execution_enabled": False,
                    "autopilot_execution_enabled": False,
                }
            ),
        ),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "meta_execution_scope_not_locked" in result["blockers"]
    assert "dev_show_tokens_not_locked" in result["blockers"]


def test_live_preflight_distinguishes_missing_legal_page(monkeypatch):
    responses = {
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(_safe_beta_readiness_payload())),
        "https://vexmera.com/privacy": (404, ""),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "privacy_page_unreachable" in result["blockers"]
