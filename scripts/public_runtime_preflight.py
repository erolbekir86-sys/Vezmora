from __future__ import annotations

import json
from typing import Any

from scripts.pilot_preflight import _get_text


def _safe_json_get(url: str) -> tuple[int | None, bool, dict[str, object]]:
    """Fetch one public diagnostics endpoint and fail closed on invalid JSON/errors."""
    try:
        status, body = _get_text(url)
        reachable = status == 200
        payload = json.loads(body) if reachable else {}
        if not isinstance(payload, dict):
            return status, False, {}
        return status, reachable, payload
    except (RuntimeError, json.JSONDecodeError):
        return None, False, {}


def build_public_runtime_preflight(base_url: str) -> dict[str, Any]:
    """Check non-secret production runtime and private-beta safety evidence.

    Both endpoints expose only booleans and deployment metadata intended for
    diagnostics. This helper never sends credentials or performs mutations.
    It fails closed on infrastructure or execution-lock conditions that would
    make private-beta onboarding unsafe, while leaving provider-specific/manual
    gates to the existing pilot runbook.
    """
    base = base_url.rstrip("/")
    blockers: list[str] = []

    runtime_status, runtime_reachable, runtime = _safe_json_get(f"{base}/health/runtime")
    beta_status, beta_reachable, beta = _safe_json_get(f"{base}/health/beta-readiness")

    vercel = runtime.get("vercel") is True
    production_env = runtime.get("vercel_env") == "production"
    database_connection_ok = runtime.get("database_connection_ok") is True
    internal_secrets_configured = runtime.get("internal_secrets_configured") is True
    commit_sha_present = bool(str(runtime.get("git_commit_sha") or "").strip())

    if not runtime_reachable:
        blockers.append("runtime_unreachable")
    else:
        if not vercel:
            blockers.append("runtime_not_vercel")
        if not production_env:
            blockers.append("runtime_not_production")
        if not database_connection_ok:
            blockers.append("database_connection_unhealthy")
        if not internal_secrets_configured:
            blockers.append("internal_secrets_not_configured")
        if not commit_sha_present:
            blockers.append("deployment_commit_unknown")

    private_beta_execution_safe = beta.get("private_beta_execution_safe") is True
    production_transport_safe = beta.get("production_transport_safe") is True
    external_execution_disabled = beta.get("external_execution_enabled") is False
    autopilot_execution_disabled = beta.get("autopilot_execution_enabled") is False
    meta_execution_scope_disabled = beta.get("meta_execution_scope_enabled") is False
    dev_show_tokens_disabled = beta.get("dev_show_tokens_enabled") is False

    if not beta_reachable:
        blockers.append("beta_readiness_unreachable")
    else:
        if not private_beta_execution_safe:
            blockers.append("private_beta_execution_not_safe")
        if not production_transport_safe:
            blockers.append("production_transport_not_safe")
        if not external_execution_disabled:
            blockers.append("external_execution_enabled")
        if not autopilot_execution_disabled:
            blockers.append("autopilot_execution_enabled")
        if not meta_execution_scope_disabled:
            blockers.append("meta_execution_scope_enabled")
        if not dev_show_tokens_disabled:
            blockers.append("dev_show_tokens_enabled")

    return {
        "ok": not blockers,
        "scope": "public_read_only_runtime_checks",
        "base_url": base,
        "checks": {
            "runtime": {
                "status_code": runtime_status,
                "reachable": runtime_reachable,
                "vercel": runtime.get("vercel"),
                "vercel_env": runtime.get("vercel_env"),
                "database_connection_ok": runtime.get("database_connection_ok"),
                "internal_secrets_configured": runtime.get("internal_secrets_configured"),
                "git_commit_sha_present": commit_sha_present,
                "google_oauth_configured": runtime.get("google_oauth_configured"),
                "meta_oauth_configured": runtime.get("meta_oauth_configured"),
                "smtp_configured": runtime.get("smtp_configured"),
            },
            "beta_readiness": {
                "status_code": beta_status,
                "reachable": beta_reachable,
                "private_beta_execution_safe": beta.get("private_beta_execution_safe"),
                "production_transport_safe": beta.get("production_transport_safe"),
                "external_execution_enabled": beta.get("external_execution_enabled"),
                "autopilot_execution_enabled": beta.get("autopilot_execution_enabled"),
                "meta_execution_scope_enabled": beta.get("meta_execution_scope_enabled"),
                "dev_show_tokens_enabled": beta.get("dev_show_tokens_enabled"),
                "configuration_ready": (beta.get("pilot_readiness") or {}).get("configuration_ready")
                if isinstance(beta.get("pilot_readiness"), dict)
                else None,
            },
        },
        "blockers": blockers,
        "note": (
            "GET-only runtime and beta-safety checks using non-secret deployment diagnostics. "
            "No credentials are sent and no provider, advertising, billing, or customer state is changed."
        ),
    }
