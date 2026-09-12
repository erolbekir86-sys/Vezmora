from __future__ import annotations

import json

from scripts import pilot_preflight


def _responses(payload: dict[str, object]) -> dict[str, tuple[int, str]]:
    return {
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(payload)),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }


def _safe_payload() -> dict[str, object]:
    return {
        "private_beta_execution_safe": True,
        "production_transport_safe": True,
        "external_execution_enabled": False,
        "autopilot_execution_enabled": False,
        "meta_execution_scope_enabled": False,
        "dev_show_tokens_enabled": False,
    }


def test_live_preflight_requires_production_transport_safe(monkeypatch):
    payload = _safe_payload()
    payload["production_transport_safe"] = False
    responses = _responses(payload)
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert result["checks"]["beta_readiness"]["production_transport_safe"] is False
    assert "production_transport_unsafe" in result["blockers"]


def test_live_preflight_fails_closed_when_transport_field_is_missing(monkeypatch):
    payload = _safe_payload()
    payload.pop("production_transport_safe")
    responses = _responses(payload)
    monkeypatch.setattr(pilot_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = pilot_preflight.build_live_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert result["checks"]["beta_readiness"]["production_transport_safe"] is False
    assert "production_transport_unsafe" in result["blockers"]
