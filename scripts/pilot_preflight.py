from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.beta_readiness import beta_safety_snapshot
from app.stripe_billing import CHECKOUT_PRICING_RECONCILED


def build_preflight_snapshot() -> dict[str, Any]:
    """Return a non-secret, conservative configuration preflight for pilot operators.

    The existing beta-readiness endpoint is intentionally configuration-only and
    keeps commercial pricing reconciliation as a manual gate. This operator view
    also treats the code-level Checkout pricing gate as an active blocker so a
    pilot cannot be mistaken for billing-ready while Checkout is deliberately
    disabled.

    `ok` means only that machine-checkable configuration blockers are clear. It is
    deliberately not a claim that the five-company pilot is approved or ready:
    several manual gates require external evidence that this script cannot verify.
    """
    snapshot = beta_safety_snapshot()
    pilot = dict(snapshot.get("pilot_readiness") or {})
    blockers = list(pilot.get("configuration_blockers") or [])
    manual_gates = list(pilot.get("manual_gates") or [])

    if not CHECKOUT_PRICING_RECONCILED and "checkout_pricing_reconciliation" not in blockers:
        blockers.append("checkout_pricing_reconciliation")

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
        "configuration_ready": bool(pilot.get("configuration_ready")),
        "checkout_pricing_reconciled": bool(CHECKOUT_PRICING_RECONCILED),
        "blockers": blockers,
        "manual_gates": manual_gates,
        "note": (
            "Configuration preflight only. ok=true does not mean pilot-ready. Pilot readiness remains "
            "undetermined until the listed manual gates have current evidence; this script does not prove "
            "legal approval, live connector access, browser QA, production observability, or permission "
            "to execute external ad changes."
        ),
    }


def main() -> int:
    result = build_preflight_snapshot()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
