from __future__ import annotations

import argparse
import json
import re
from typing import Any
from urllib.parse import unquote, urlsplit

from scripts.preflight_http import get_public_text, normalize_https_origin
from scripts.public_runtime_preflight import build_public_runtime_preflight

_ASSET = re.compile(r'''/static/[A-Za-z0-9_./-]+\.(?:js|css|jpg|jpeg|png|svg|webp|woff2?)(?:\?[^\s"'<>`)]*)?''')
_MAX_ASSETS = 64
_ROUTES = {
    "/": 200,
    "/app": 200,
    "/api/auth/me": 401,
    "/api/workspaces": 401,
    "/api/connectors?workspace_id=1": 401,
    "/api/dashboard?workspace_id=1": 401,
    "/docs": 404,
    "/redoc": 404,
    "/openapi.json": 404,
    "/vexmera-deployment-preflight-missing-page": 404,
}


def _get(url: str) -> tuple[int, str]:
    return get_public_text(url, user_agent="Vexmera-Public-Deployment-Preflight/1.0")


def _assets(text: str) -> set[str]:
    return {
        path for path in _ASSET.findall(text)
        if ".." not in unquote(urlsplit(path).path).split("/")
    }


def build_public_deployment_preflight(base_url: str, expected_revision: str) -> dict[str, Any]:
    """Check deployed routing, auth boundaries and packaged first-party assets.

    No credentials, browser session or provider calls are used. A revision-pinned
    runtime gate runs first. Only /static/ assets on the explicit origin are read,
    including assets referenced by the first-party loaders. Redirects and oversized
    responses are rejected by the existing shared HTTP helper.
    """
    result: dict[str, Any] = {
        "ok": False, "scope": "public_get_only_deployment_checks",
        "base_url": None, "checks": {}, "assets": {}, "blockers": [],
        "note": "Public deployment evidence only; authenticated browser flows, live providers, legal approval and billing remain separate gates.",
    }
    try:
        base = normalize_https_origin(base_url)
    except ValueError:
        result["blockers"] = ["invalid_base_url"]
        return result
    result["base_url"] = base
    if not re.fullmatch(r"[0-9a-f]{40}", expected_revision):
        result["blockers"] = ["expected_full_revision_required"]
        return result
    runtime = build_public_runtime_preflight(base, expected_revision=expected_revision)
    result["runtime"] = runtime
    if not runtime.get("ok"):
        result["blockers"] = ["runtime_gate_failed"]
        return result

    pending: set[str] = set()
    for path, expected in _ROUTES.items():
        try:
            status, text = _get(base + path)
            passed = status == expected and (bool(text.strip()) if expected == 200 else True)
            result["checks"][path] = {"expected_status": expected, "status_code": status, "ok": passed}
            if not passed:
                result["blockers"].append(f"route_failed:{path}")
            if expected == 200 and passed:
                pending.update(_assets(text))
        except RuntimeError:
            result["checks"][path] = {"expected_status": expected, "status_code": None, "ok": False}
            result["blockers"].append(f"route_unreachable:{path}")

    while pending:
        path = min(pending)
        pending.remove(path)
        if path in result["assets"]:
            continue
        if len(result["assets"]) >= _MAX_ASSETS:
            result["blockers"].append("asset_limit_exceeded")
            break
        try:
            status, text = _get(base + path)
            passed = status == 200 and bool(text.strip())
            result["assets"][path] = {"status_code": status, "ok": passed}
            if not passed:
                result["blockers"].append(f"asset_failed:{path}")
            elif urlsplit(path).path.endswith((".js", ".css")):
                pending.update(_assets(text) - result["assets"].keys())
        except RuntimeError:
            result["assets"][path] = {"status_code": None, "ok": False}
            result["blockers"].append(f"asset_unreachable:{path}")
    if not result["assets"]:
        result["blockers"].append("no_first_party_assets_found")
    result["ok"] = not result["blockers"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Revision-pinned GET-only Vexmera deployment checks")
    parser.add_argument("--base-url", default="https://vexmera.com")
    parser.add_argument("--expected-revision", required=True, help="Exact 40-character production commit SHA")
    args = parser.parse_args(argv)
    result = build_public_deployment_preflight(args.base_url, args.expected_revision)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
