from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _get_text(url: str, timeout: float = 8.0) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "Vexmera-Public-Legal-Preflight/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return int(exc.code), ""
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"request_failed:{type(exc).__name__}") from exc


def build_public_legal_preflight(base_url: str) -> dict[str, Any]:
    """Verify public legal discoverability using GET requests only.

    This intentionally checks only public pages. It sends no credentials and
    performs no mutations. The goal is to catch a subtle but important failure
    mode for pilot/OAuth readiness: legal pages may exist while the marketing
    homepage stops linking to them.
    """
    base = base_url.rstrip("/")
    checks: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []

    try:
        status, home = _get_text(f"{base}/")
        reachable = status == 200
        privacy_linked = reachable and ('href="/privacy"' in home or f'href="{base}/privacy"' in home)
        terms_linked = reachable and ('href="/terms"' in home or f'href="{base}/terms"' in home)
        checks["homepage"] = {
            "status_code": status,
            "reachable": reachable,
            "privacy_linked": privacy_linked,
            "terms_linked": terms_linked,
        }
        if not reachable:
            blockers.append("homepage_unreachable")
        else:
            if not privacy_linked:
                blockers.append("privacy_not_linked_from_homepage")
            if not terms_linked:
                blockers.append("terms_not_linked_from_homepage")
    except RuntimeError:
        checks["homepage"] = {
            "reachable": False,
            "privacy_linked": False,
            "terms_linked": False,
        }
        blockers.append("homepage_unreachable")

    expectations = {
        "privacy": ("/privacy", ("Integritetspolicy", "Google API Services User Data Policy")),
        "terms": ("/terms", ("Terms of Service", "Vexmera")),
    }
    for name, (path, markers) in expectations.items():
        try:
            status, body = _get_text(f"{base}{path}")
            reachable = status == 200
            expected_content_present = reachable and all(marker in body for marker in markers)
            checks[name] = {
                "status_code": status,
                "reachable": reachable,
                "expected_content_present": expected_content_present,
            }
            if not reachable:
                blockers.append(f"{name}_page_unreachable")
            elif not expected_content_present:
                blockers.append(f"{name}_page_unexpected_content")
        except RuntimeError:
            checks[name] = {"reachable": False, "expected_content_present": False}
            blockers.append(f"{name}_page_unreachable")

    return {
        "ok": not blockers,
        "scope": "public_get_only_legal_discoverability",
        "base_url": base,
        "checks": checks,
        "blockers": blockers,
        "note": "GET-only public checks. No credentials are sent and no application, billing, or advertising state is changed.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vexmera public legal discoverability preflight")
    parser.add_argument("--base-url", default="https://vexmera.com")
    args = parser.parse_args(argv)

    result = build_public_legal_preflight(args.base_url)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
