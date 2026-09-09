from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.beta_readiness import beta_safety_snapshot
from app.pricing import checkout_pricing_reconciled


def _checkout_pricing_reconciled() -> bool:
    return checkout_pricing_reconciled()


def build_preflight_snapshot() -> dict[str, Any]:
    """Return a non-secret, conservative configuration preflight for pilot operators.

    The existing beta-readiness endpoint is intentionally configuration-only.
    This operator view also treats the explicit current-pricing Checkout gate and
    missing internal security secrets as active blockers so a pilot cannot be
    mistaken for ready while billing is deliberately disabled or token/maintenance
    protections are absent.

    `ok` means only that machine-checkable configuration blockers are clear. It is
    deliberately not a claim that the five-company pilot is approved or ready:
    several manual gates require external evidence that this script cannot verify.
    """
    snapshot = beta_safety_snapshot()
    pilot = dict(snapshot.get("pilot_readiness") or {})
    blockers = list(pilot.get("configuration_blockers") or [])
    manual_gates = list(pilot.get("manual_gates") or [])
    pricing_reconciled = _checkout_pricing_reconciled()

    if not pricing_reconciled and "checkout_pricing_reconciliation" not in blockers:
        blockers.append("checkout_pricing_reconciliation")

    core_internal_secrets_configured = snapshot.get("core_internal_secrets_configured") is not False
    if not core_internal_secrets_configured and "core_internal_secrets_configured" not in blockers:
        blockers.append("core_internal_secrets_configured")

    configuration_ok = not blockers
    manual_verification_required = bool(manual_gates)
    if not configuration_ok:
        status = "configuration_blocked"
    elif manual_verification_required:
        status = "manual_verification_required"
    else:
        status = "configuration_clear"

    return {
        "ok": configuration_ok,
        "ok_scope": "configuration_only",
        "status": status,
        "pilot_ready": None,
        "manual_verification_required": manual_verification_required,
        "phase": snapshot.get("phase"),
        "private_beta_execution_safe": bool(snapshot.get("private_beta_execution_safe")),
        "production_transport_safe": bool(snapshot.get("production_transport_safe")),
        "core_internal_secrets_configured": core_internal_secrets_configured,
        "configuration_ready": bool(pilot.get("configuration_ready")),
        "checkout_pricing_reconciled": pricing_reconciled,
        "blockers": blockers,
        "manual_gates": manual_gates,
        "note": (
            "Configuration preflight only. ok=true does not mean pilot-ready. Pilot readiness remains "
            "undetermined until the listed manual gates have current evidence; this script does not prove "
            "legal approval, live connector access, browser QA, production observability, or permission "
            "to execute external ad changes."
        ),
    }


def _get_text(url: str, timeout: float = 8.0) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "Vexmera-Pilot-Preflight/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return int(exc.code), ""
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"request_failed:{type(exc).__name__}") from exc


def build_live_preflight(base_url: str) -> dict[str, Any]:
    """Read only public production endpoints and report pilot-safety evidence.

    This function performs GET requests only. It never sends credentials, mutates
    provider state, changes campaigns, or reads secret values.
    """
    base = base_url.rstrip("/")
    checks: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []

    try:
        status, body = _get_text(f"{base}/health/beta-readiness")
        health_ok = status == 200
        payload = json.loads(body) if health_ok else {}
        execution_safe = payload.get("private_beta_execution_safe") is True
        external_locked = payload.get("external_execution_enabled") is False
        autopilot_locked = payload.get("autopilot_execution_enabled") is False
        meta_execution_scope_locked = payload.get("meta_execution_scope_enabled") is False
        dev_show_tokens_locked = payload.get("dev_show_tokens_enabled") is False
        checks["beta_readiness"] = {
            "status_code": status,
            "reachable": health_ok,
            "private_beta_execution_safe": execution_safe,
            "external_execution_enabled": payload.get("external_execution_enabled"),
            "autopilot_execution_enabled": payload.get("autopilot_execution_enabled"),
            "meta_execution_scope_enabled": payload.get("meta_execution_scope_enabled"),
            "dev_show_tokens_enabled": payload.get("dev_show_tokens_enabled"),
        }
        if not health_ok:
            blockers.append("beta_readiness_unreachable")
        if health_ok and not execution_safe:
            blockers.append("private_beta_execution_unsafe")
        if health_ok and not external_locked:
            blockers.append("external_execution_not_locked")
        if health_ok and not autopilot_locked:
            blockers.append("autopilot_execution_not_locked")
        if health_ok and not meta_execution_scope_locked:
            blockers.append("meta_execution_scope_not_locked")
        if health_ok and not dev_show_tokens_locked:
            blockers.append("dev_show_tokens_not_locked")
    except (RuntimeError, json.JSONDecodeError):
        checks["beta_readiness"] = {"reachable": False}
        blockers.append("beta_readiness_unreachable")

    legal_expectations = {
        "privacy": ("/privacy", "Integritetspolicy", "Google API Services User Data Policy"),
        "terms": ("/terms", "Terms of Service", "Vexmera"),
    }
    for name, (path, marker_a, marker_b) in legal_expectations.items():
        try:
            status, body = _get_text(f"{base}{path}")
            reachable = status == 200
            content_ok = reachable and marker_a in body and marker_b in body
            checks[name] = {
                "status_code": status,
                "reachable": reachable,
                "expected_content_present": content_ok,
            }
            if not reachable:
                blockers.append(f"{name}_page_unreachable")
            elif not content_ok:
                blockers.append(f"{name}_page_unexpected_content")
        except RuntimeError:
            checks[name] = {"reachable": False, "expected_content_present": False}
            blockers.append(f"{name}_page_unreachable")

    return {
        "ok": not blockers,
        "scope": "public_read_only_live_checks",
        "base_url": base,
        "checks": checks,
        "blockers": blockers,
        "note": "GET-only production checks. No credentials are sent and no external advertising state is changed.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vexmera five-company pilot safety preflight")
    parser.add_argument(
        "--base-url",
        help="Optionally run GET-only checks against public endpoints, e.g. https://vexmera.com",
    )
    args = parser.parse_args(argv)

    result = build_preflight_snapshot()
    if args.base_url:
        result["live"] = build_live_preflight(args.base_url)

    print(json.dumps(result, indent=2, sort_keys=True))
    ok = result["ok"] and result.get("live", {"ok": True})["ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
