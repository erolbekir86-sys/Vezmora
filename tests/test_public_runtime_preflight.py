from __future__ import annotations

import json

from scripts import public_runtime_preflight


def _safe_runtime_payload() -> dict[str, object]:
    return {
        "ok": True,
        "service": "vexmera",
        "version": "0.6.1",
        "platform": "vercel",
        "environment": "production",
        "deployment_revision": "abc123",
    }


def _safe_beta_payload() -> dict[str, object]:
    return {
        "ok": True,
        "phase": "private_beta",
        "private_beta_execution_safe": True,
        "production_transport_safe": True,
        "external_execution_enabled": False,
        "autopilot_execution_enabled": False,
        "meta_execution_scope_enabled": False,
        "dev_show_tokens_enabled": False,
    }


def _response_map(runtime: dict[str, object] | None = None, beta: dict[str, object] | None = None):
    responses = {
        "https://vexmera.com/health/runtime": (200, json.dumps(runtime or _safe_runtime_payload())),
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(beta or _safe_beta_payload())),
    }
    return lambda url, timeout=8.0: responses[url]


def test_public_runtime_preflight_passes_minimal_runtime_and_execution_lock(monkeypatch):
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map())

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com/")

    assert result["ok"] is True
    assert result["blockers"] == []
    runtime = result["checks"]["runtime"]
    assert runtime["reachable"] is True
    assert runtime["platform"] == "vercel"
    assert runtime["environment"] == "production"
    assert runtime["deployment_revision_present"] is True
    assert runtime["revision_match_required"] is False
    assert runtime["deployment_revision_matches_expected"] is None
    beta = result["checks"]["beta_readiness"]
    assert beta["reachable"] is True
    assert beta["private_beta_execution_safe"] is True
    assert beta["production_transport_safe"] is True
    assert beta["external_execution_enabled"] is False
    assert beta["autopilot_execution_enabled"] is False


def test_public_runtime_preflight_can_pin_expected_revision(monkeypatch):
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map())

    result = public_runtime_preflight.build_public_runtime_preflight(
        "https://vexmera.com",
        expected_revision="abc123",
    )

    assert result["ok"] is True
    runtime = result["checks"]["runtime"]
    assert runtime["revision_match_required"] is True
    assert runtime["deployment_revision_matches_expected"] is True


def test_public_runtime_preflight_blocks_revision_mismatch(monkeypatch):
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map())

    result = public_runtime_preflight.build_public_runtime_preflight(
        "https://vexmera.com",
        expected_revision="def456",
    )

    assert result["ok"] is False
    assert "deployment_revision_mismatch" in result["blockers"]
    runtime = result["checks"]["runtime"]
    assert runtime["revision_match_required"] is True
    assert runtime["deployment_revision_matches_expected"] is False


def test_public_runtime_preflight_fails_closed_on_invalid_deployment_identity(monkeypatch):
    payload = _safe_runtime_payload()
    payload.update(
        {
            "platform": "other",
            "environment": "preview",
            "deployment_revision": None,
        }
    )
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map(runtime=payload))

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "runtime_not_vercel" in result["blockers"]
    assert "runtime_not_production" in result["blockers"]
    assert "deployment_revision_unknown" in result["blockers"]


def test_public_runtime_preflight_blocks_if_execution_lock_is_unsafe(monkeypatch):
    beta = _safe_beta_payload()
    beta.update(
        {
            "private_beta_execution_safe": False,
            "external_execution_enabled": True,
            "autopilot_execution_enabled": True,
            "meta_execution_scope_enabled": True,
            "dev_show_tokens_enabled": True,
        }
    )
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map(beta=beta))

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "private_beta_execution_not_safe" in result["blockers"]
    assert "external_execution_enabled" in result["blockers"]
    assert "autopilot_execution_enabled" in result["blockers"]
    assert "meta_execution_scope_enabled" in result["blockers"]
    assert "dev_show_tokens_enabled" in result["blockers"]


def test_public_runtime_preflight_blocks_if_production_transport_is_unsafe(monkeypatch):
    beta = _safe_beta_payload()
    beta["production_transport_safe"] = False
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map(beta=beta))

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "production_transport_not_safe" in result["blockers"]
    assert result["checks"]["beta_readiness"]["production_transport_safe"] is False


def test_public_runtime_preflight_distinguishes_unreachable_runtime_endpoint(monkeypatch):
    responses = {
        "https://vexmera.com/health/runtime": (503, ""),
        "https://vexmera.com/health/beta-readiness": (200, json.dumps(_safe_beta_payload())),
    }
    monkeypatch.setattr(public_runtime_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert result["blockers"] == ["runtime_unreachable"]
    assert result["checks"]["runtime"]["reachable"] is False
    assert result["checks"]["beta_readiness"]["reachable"] is True


def test_public_runtime_preflight_distinguishes_unreachable_beta_endpoint(monkeypatch):
    responses = {
        "https://vexmera.com/health/runtime": (200, json.dumps(_safe_runtime_payload())),
        "https://vexmera.com/health/beta-readiness": (503, ""),
    }
    monkeypatch.setattr(public_runtime_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert result["blockers"] == ["beta_readiness_unreachable"]
    assert result["checks"]["beta_readiness"]["reachable"] is False


def test_public_runtime_preflight_does_not_render_unexpected_fields(monkeypatch):
    secret = "super-secret-value"
    runtime = _safe_runtime_payload()
    runtime["accidental_secret_field"] = secret
    beta = _safe_beta_payload()
    beta["another_accidental_secret"] = secret
    monkeypatch.setattr(public_runtime_preflight, "_get_text", _response_map(runtime=runtime, beta=beta))

    rendered = json.dumps(
        public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com"),
        sort_keys=True,
    )

    assert secret not in rendered
    assert "accidental_secret_field" not in rendered
    assert "another_accidental_secret" not in rendered
