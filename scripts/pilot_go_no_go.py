from __future__ import annotations

import argparse
import json
from typing import Any

from scripts.pilot_preflight import build_live_preflight, build_preflight_snapshot
from scripts.public_legal_preflight import build_public_legal_preflight
from scripts.public_runtime_preflight import build_public_runtime_preflight


def build_go_no_go_snapshot(
    base_url: str | None = None,
    expected_revision: str | None = None,
) -> dict[str, Any]:
    """Combine existing non-mutating pilot checks into one operator snapshot.

    This deliberately does not claim that the pilot is approved. It only combines
    machine-checkable configuration, public execution-lock evidence, runtime health
    and public legal discoverability. Manual gates in the pilot runbook remain mandatory.
    When an expected revision is supplied, deployed runtime identity must match it.
    """
    configuration = build_preflight_snapshot()
    result: dict[str, Any] = {
        "ok": bool(configuration.get("ok")),
        "scope": "machine_checks_only",
        "pilot_ready": None,
        "configuration": configuration,
        "manual_verification_required": bool(configuration.get("manual_verification_required", True)),
        "note": (
            "Machine checks only. ok=true does not approve the five-company pilot. "
            "Complete all current manual gates in FIVE_COMPANY_PILOT_RUNBOOK.md before onboarding."
        ),
    }

    if base_url:
        live = build_live_preflight(base_url)
        runtime = (
            build_public_runtime_preflight(base_url, expected_revision=expected_revision)
            if expected_revision
            else build_public_runtime_preflight(base_url)
        )
        legal = build_public_legal_preflight(base_url)
        result["live"] = live
        result["runtime"] = runtime
        result["legal_discoverability"] = legal
        result["ok"] = bool(
            result["ok"] and live.get("ok") and runtime.get("ok") and legal.get("ok")
        )

    result["status"] = "machine_checks_clear" if result["ok"] else "blocked"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vexmera five-company pilot consolidated read-only preflight")
    parser.add_argument(
        "--base-url",
        help="Optionally add GET-only deployed checks, e.g. https://vexmera.com",
    )
    parser.add_argument(
        "--expected-revision",
        help="Optional exact deployment revision expected from /health/runtime",
    )
    args = parser.parse_args(argv)

    result = build_go_no_go_snapshot(args.base_url, expected_revision=args.expected_revision)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
