from __future__ import annotations

import json
from typing import Any

from scripts.pilot_preflight import _get_text
from scripts.preflight_http import normalize_https_origin


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


def build_public_runtime_preflight(
    base_url: str,
    expected_revision: str | None = None,
) -> dict[str, Any]:
    """Check minimal production identity and private-beta execution safety.

    Public runtime diagnostics intentionally expose only liveness and deployment
    identity. Provider configuration, database health and secret-presence checks
    belong in authenticated/operator tooling rather than on a public endpoint.
    This helper remains GET-only and fails closed when the production identity or
    private-beta execution lock cannot be verified. When an expected deployment
    revision is supplied by the operator, the active runtime must match it exactly.
    """
    try:
        base = normalize_https_origin(base_url)
    except ValueError:
        return {
            "ok": False,
            "scope": "public_read_only_runtime_checks",
            "base_url": None,
            "checks": {},
            "blockers": ["invalid_base_url"],
            "note": "Runtime preflight requires a plain HTTPS origin and never follows redirects.",
        }

    blockers: list[str] = []

    runtime_status, runtime_reachable, runtime = _safe_json_get(f"{base}/health/runtime")
    beta_status, beta_reachable, beta = _safe_json_get(f"{base}/health/beta-readiness")

    platform_vercel = runtime.get("platform") == "vercel"
    production_env = runtime.get("environment") == "production"
    deployment_revision = str(runtime.get("deployment_revision") or "").strip()
    deployment_revision_present = bool(deployment_revision)
    normalized_expected_revision = str(expected_revision or "").strip()
    revision_match_required = bool(normalized_expected_revision)
    deployment_revision_matches_expected = (
        deployment_revision == normalized_expected_revision
        if revision_match_required and deployment_revision_present
        else None
    )

    if not runtime_reachable:
        blockers.append("runtime_unreachable")
    else:
        if not platform_vercel:
            blockers.append("runtime_not_vercel")
        if not production_env:
            blockers.append("runtime_not_production")
        if not deployment_revision_present:
            blockers.append("deployment_revision_unknown")
        elif revision_match_required and not deployment_revision_matches_expected:
            blockers.append("deployment_revision_mismatch")

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
                "platform": runtime.get("platform"),
                "environment": runtime.get("environment"),
                "deployment_revision_present": deployment_revision_present,
                "revision_match_required": revision_match_required,
                "deployment_revision_matches_expected": deployment_revision_matches_expected,
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
            },
        },
        "blockers": blockers,
        "note": (
            "GET-only checks against one explicit HTTPS origin using minimal public deployment identity and "
            "private-beta safety evidence. Redirects are rejected and responses are size-bounded. Database, "
            "provider and secret-presence diagnostics are intentionally not exposed publicly."
        ),
    }
