from __future__ import annotations

import json
from typing import Any

from scripts.pilot_preflight import _get_text


def build_public_runtime_preflight(base_url: str) -> dict[str, Any]:
    """Check non-secret production runtime evidence using a single GET request.

    The endpoint already exposes booleans and deployment metadata intended for
    diagnostics. This helper never sends credentials or performs mutations.
    It fails closed on infrastructure conditions that would make a private-beta
    onboarding unreliable, while leaving provider-specific/manual gates to the
    existing pilot runbook.
    """
    base = base_url.rstrip("/")
    blockers: list[str] = []

    try:
        status, body = _get_text(f"{base}/health/runtime")
        reachable = status == 200
        payload = json.loads(body) if reachable else {}
    except (RuntimeError, json.JSONDecodeError):
        status = None
        reachable = False
        payload = {}

    vercel = payload.get("vercel") is True
    production_env = payload.get("vercel_env") == "production"
    database_connection_ok = payload.get("database_connection_ok") is True
    internal_secrets_configured = payload.get("internal_secrets_configured") is True
    commit_sha_present = bool(str(payload.get("git_commit_sha") or "").strip())

    if not reachable:
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

    return {
        "ok": not blockers,
        "scope": "public_read_only_runtime_checks",
        "base_url": base,
        "checks": {
            "runtime": {
                "status_code": status,
                "reachable": reachable,
                "vercel": payload.get("vercel"),
                "vercel_env": payload.get("vercel_env"),
                "database_connection_ok": payload.get("database_connection_ok"),
                "internal_secrets_configured": payload.get("internal_secrets_configured"),
                "git_commit_sha_present": commit_sha_present,
                "google_oauth_configured": payload.get("google_oauth_configured"),
                "meta_oauth_configured": payload.get("meta_oauth_configured"),
                "smtp_configured": payload.get("smtp_configured"),
            }
        },
        "blockers": blockers,
        "note": (
            "GET-only runtime checks using non-secret deployment diagnostics. "
            "No credentials are sent and no provider, advertising, billing, or customer state is changed."
        ),
    }
