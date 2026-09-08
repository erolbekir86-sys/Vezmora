from __future__ import annotations

import json

from scripts import public_runtime_preflight


def _safe_runtime_payload() -> dict[str, object]:
    return {
        "ok": True,
        "brand": "Vexmera",
        "vercel": True,
        "vercel_env": "production",
        "git_commit_sha": "abc123",
        "database_connection_ok": True,
        "internal_secrets_configured": True,
        "google_oauth_configured": True,
        "meta_oauth_configured": False,
        "smtp_configured": True,
    }


def test_public_runtime_preflight_passes_safe_runtime(monkeypatch):
    monkeypatch.setattr(
        public_runtime_preflight,
        "_get_text",
        lambda url, timeout=8.0: (200, json.dumps(_safe_runtime_payload())),
    )

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com/")

    assert result["ok"] is True
    assert result["blockers"] == []
    runtime = result["checks"]["runtime"]
    assert runtime["reachable"] is True
    assert runtime["vercel"] is True
    assert runtime["vercel_env"] == "production"
    assert runtime["database_connection_ok"] is True
    assert runtime["internal_secrets_configured"] is True
    assert runtime["git_commit_sha_present"] is True


def test_public_runtime_preflight_fails_closed_on_unhealthy_infrastructure(monkeypatch):
    payload = _safe_runtime_payload()
    payload.update(
        {
            "vercel": False,
            "vercel_env": "preview",
            "git_commit_sha": None,
            "database_connection_ok": False,
            "internal_secrets_configured": False,
        }
    )
    monkeypatch.setattr(
        public_runtime_preflight,
        "_get_text",
        lambda url, timeout=8.0: (200, json.dumps(payload)),
    )

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "runtime_not_vercel" in result["blockers"]
    assert "runtime_not_production" in result["blockers"]
    assert "database_connection_unhealthy" in result["blockers"]
    assert "internal_secrets_not_configured" in result["blockers"]
    assert "deployment_commit_unknown" in result["blockers"]


def test_public_runtime_preflight_distinguishes_unreachable_endpoint(monkeypatch):
    monkeypatch.setattr(
        public_runtime_preflight,
        "_get_text",
        lambda url, timeout=8.0: (503, ""),
    )

    result = public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert result["blockers"] == ["runtime_unreachable"]
    assert result["checks"]["runtime"]["reachable"] is False


def test_public_runtime_preflight_does_not_render_secret_values(monkeypatch):
    secret = "super-secret-value"
    payload = _safe_runtime_payload()
    payload["accidental_secret_field"] = secret
    monkeypatch.setattr(
        public_runtime_preflight,
        "_get_text",
        lambda url, timeout=8.0: (200, json.dumps(payload)),
    )

    rendered = json.dumps(
        public_runtime_preflight.build_public_runtime_preflight("https://vexmera.com"),
        sort_keys=True,
    )

    assert secret not in rendered
    assert "accidental_secret_field" not in rendered
