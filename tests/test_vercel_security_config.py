from __future__ import annotations

import json
from pathlib import Path


def test_vercel_config_sets_minimal_csp_without_restricting_app_assets():
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))

    header_rules = config.get("headers") or []
    global_rule = next((rule for rule in header_rules if rule.get("source") == "/(.*)"), None)

    assert global_rule is not None
    headers = {item["key"].lower(): item["value"] for item in global_rule.get("headers", [])}
    assert headers["content-security-policy"] == (
        "base-uri 'self'; object-src 'none'; form-action 'self'; frame-ancestors 'none'"
    )
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert headers["x-permitted-cross-domain-policies"] == "none"

    # Keep this deliberately narrow for Private Beta. These directives harden
    # injected <base>, plugin/object content, cross-origin HTML form posts, and
    # clickjacking without changing script/style, API, OAuth, analytics, or
    # payment origins.
    csp = headers["content-security-policy"]
    assert "form-action 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "default-src" not in csp
    assert "script-src" not in csp
    assert "style-src" not in csp
    assert "connect-src" not in csp
