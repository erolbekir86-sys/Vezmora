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
    """Return a non-secret, conservative preflight summary for pilot operators.

    The existing beta-readiness endpoint is intentionally configuration-only and
    keeps commercial pricing reconciliation as a manual gate. This operator view
    also treats the code-level Checkout pricing gate as an active blocker so a
    pilot cannot be mistaken for billing-ready while Checkout is deliberately
    disabled.
    """
    snapshot = beta_safety_snapshot()
    pilot = dict(snapshot.get("pilot_readiness") or {})
    blockers = list(pilot.get("configuration_blockers") or [])

    if not CHECKOUT_PRICING_RECONCILED:
        blockers.append("checkout_pricing_reconciliation")

    return {
        "ok": not blockers,
        "phase": snapshot.get("phase"),
        "private_beta_execution_safe": bool(snapshot.get("private_beta_execution_safe")),
        "production_transport_safe": bool(snapshot.get("production_transport_safe")),
        "configuration_ready": bool(pilot.get("configuration_ready")),
        "checkout_pricing_reconciled": bool(CHECKOUT_PRICING_RECONCILED),
        "blockers": blockers,
        "manual_gates": list(pilot.get("manual_gates") or []),
        "note": (
            "Configuration preflight only. It does not prove legal approval, live connector access, "
            "browser QA, production observability, or permission to execute external ad changes."
        ),
    }


def main() -> int:
    result = build_preflight_snapshot()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
